import kopf
import yaml
import kubernetes
import time
from jinja2 import Environment, FileSystemLoader


def wait_until_job_end(jobname, namespace):
    api = kubernetes.client.BatchV1Api()
    job_finished = False
    jobs = api.list_namespaced_job(namespace)
    while (not job_finished) and \
            any(job.metadata.name == jobname for job in jobs.items):
        time.sleep(1)
        jobs = api.list_namespaced_job(namespace)
        for job in jobs.items:
            if job.metadata.name == jobname:
                print(f"job with { jobname }  found,wait untill end")
                if job.status.succeeded == 1:
                    print(f"job with { jobname }  success")
                    job_finished = True


def render_template(filename, vars_dict):
    env = Environment(loader=FileSystemLoader('./templates'))
    template = env.get_template(filename)
    yaml_manifest = template.render(vars_dict)
    json_manifest = yaml.load(yaml_manifest)
    return json_manifest


def delete_success_jobs(mysql_instance_name, namespace):
    print("start deletion")
    api = kubernetes.client.BatchV1Api()
    jobs = api.list_namespaced_job(namespace)
    for job in jobs.items:
        jobname = job.metadata.name
        if (jobname == f"backup-{mysql_instance_name}-job") or \
                (jobname == f"restore-{mysql_instance_name}-job"):
            if job.status.succeeded == 1:
                api.delete_namespaced_job(jobname,
                                          namespace,
                                          propagation_policy='Background')


@kopf.on.create('otus.homework', 'v1', 'mysqls')
# Функция, которая будет запускаться при создании объектов тип MySQL:
def mysql_on_create(body, spec, **kwargs):
    name = body['metadata']['name']
    namespace = body['metadata']['namespace']
    image = body['spec']['image']
    password = body['spec']['password']
    database = body['spec']['database']
    storage_size = body['spec']['storage_size']

    # Генерируем JSON манифесты для деплоя
    persistent_volume = render_template('mysql-pv.yml.j2',
                                        {'name': name,
                                         'storage_size': storage_size})
    persistent_volume_claim = render_template('mysql-pvc.yml.j2',
                                              {'name': name,
                                               'storage_size': storage_size})
    service = render_template('mysql-service.yml.j2', {'name': name})

    deployment = render_template('mysql-deployment.yml.j2', {
        'name': name,
        'image': image,
        'password': password,
        'database': database})
    restore_job = render_template('restore-job.yml.j2', {
        'name': name,
        'image': image,
        'password': password,
        'database': database})

    # Определяем, что созданные ресурсы являются дочерними к управляемому CustomResource:
    kopf.append_owner_reference(persistent_volume, owner=body)
    kopf.append_owner_reference(persistent_volume_claim, owner=body)  # addopt
    kopf.append_owner_reference(service, owner=body)
    kopf.append_owner_reference(deployment, owner=body)
    # ^ Таким образом при удалении CR удалятся все, связанные с ним pv,pvc,svc, deployments

    api = kubernetes.client.CoreV1Api()
    # Создаем mysql PV:
    api.create_persistent_volume(persistent_volume)
    # Создаем mysql PVC:
    api.create_namespaced_persistent_volume_claim(namespace, persistent_volume_claim)
    # Создаем mysql SVC:
    api.create_namespaced_service(namespace, service)

    # Создаем mysql Deployment:
    api = kubernetes.client.AppsV1Api()
    api.create_namespaced_deployment(namespace, deployment)
    # Пытаемся восстановиться из backup
    try:
        api = kubernetes.client.BatchV1Api()
        api.create_namespaced_job(namespace, restore_job)
        time.sleep(60)
        jobs = api.list_namespaced_job(namespace)
        for job in jobs.items:
            jobname = job.metadata.name
            
            if (jobname == f"restore-{name}-job"):
                print("Find recovery job: " + jobname)
                if (job.status.succeeded == 1):
                    body["status"] = dict(message="mysql-instance created with restore-job")
                else:
                    body["status"] = dict(message="mysql-instance created with restore-job. But job works long time")
    except kubernetes.client.rest.ApiException:
        body["status"] = dict(message="mysql-instance created without restore-job")       

    # Cоздаем PVC  и PV для бэкапов:
    try:
        backup_pv = render_template('backup-pv.yml.j2', {'name': name})
        api = kubernetes.client.CoreV1Api()
        print(api.create_persistent_volume(backup_pv))
        api.create_persistent_volume(backup_pv)
    except kubernetes.client.rest.ApiException:
        pass

    try:
        backup_pvc = render_template('backup-pvc.yml.j2', {'name': name})
        api = kubernetes.client.CoreV1Api()
        api.create_namespaced_persistent_volume_claim(namespace, backup_pvc)
    except kubernetes.client.rest.ApiException:
        pass

    return body["status"]

@kopf.on.delete('otus.homework', 'v1', 'mysqls')
def delete_object_make_backup(body, **kwargs):
    name = body['metadata']['name']
    namespace = body['metadata']['namespace']
    image = body['spec']['image']
    password = body['spec']['password']
    database = body['spec']['database']

    delete_success_jobs(name, namespace)

    # Cоздаем backup job:
    api = kubernetes.client.BatchV1Api()
    backup_job = render_template('backup-job.yml.j2', {
        'name': name,
        'image': image,
        'password': password,
        'database': database})
    api.create_namespaced_job(namespace, backup_job)
    wait_until_job_end(f"backup-{name}-job", namespace)

    restore_job = render_template('restore-job.yml.j2', {
        'name': name,
        'image': image,
        'password': password,
        'database': database})

    print("Start deletion my recovery:  ========================= ")
    api = kubernetes.client.BatchV1Api()
    jobs = api.list_namespaced_job(namespace)
    for job in jobs.items:
        jobname = job.metadata.name
        if (jobname == f"restore-{name}-job"):
            print("Start delete recovery: " + jobname)
            api.delete_namespaced_job(jobname, namespace, propagation_policy='Background')
    print("Stop deletion my recovery:  ========================= ")
    return {'message': "mysql and its children resources deleted"}

@kopf.on.update('otus.homework', 'v1', 'mysqls')
def update_object_password(body, meta, **kwargs):
    print("=====================")
    print("Start update password")
    name = body['metadata']['name']
    namespace = body['metadata']['namespace']
    image = body['spec']['image']
    new_password = body['spec']['password']
    database = body['spec']['database']

    delete_success_jobs(name, namespace)

    last_config = yaml.load(meta.get('annotations')['kopf.zalando.org/last-handled-configuration'])
    old_password = last_config['spec']['password']

    api = kubernetes.client.BatchV1Api()
    passwd_job = render_template('mysql-change-password.yml.j2', {
        'name': name,
        'image': image,
        'old_password': old_password,
        'new_password': new_password,
        'database': database})

    api.create_namespaced_job(namespace, passwd_job)
    wait_until_job_end(f"change-password-{name}-job", namespace)
    
    kopf.event(body,
                    type='Info',
                    reason='Password',
                    message='Update password')
    
    print("End update password")
    print("=====================")
    
    return {'message': "mysql password changed"}