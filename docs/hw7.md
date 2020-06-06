
# Домашняя работа 7 (operators)

## 1 Dockerfile 
```
FROM python:3.7
COPY templates ./templates
COPY mysql-operator.py ./mysql-operator.py
RUN pip install kopf kubernetes pyyaml jinja2
CMD kopf run /mysql-operator.py
```

Отправляем в DockerHub
```
$ docker build ./build/ --tag ustinsky/mysql-operator:v0.0.2
$ docker login
$ docker push ustinsky/mysql-operator:v0.0.2
```

## 2 Запустим minikube
```
$ minikube start
```

## 3 Применим манифесты
```
$ kubectl apply -f deploy/crd.yml && \
  kubectl apply -f deploy/service-account.yml && \
  kubectl apply -f deploy/role.yml && \
  kubectl apply -f deploy/role-binding.yml && \
  kubectl apply -f deploy/deploy-operator.yml && \
  kubectl apply -f deploy/cr.yml
```

## 4 Проверяем
```
$ kubectl get pvc
NAME                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
backup-mysql-instance-pvc   Bound    pvc-5f06a495-0624-49d7-aac0-4682b2cfaba2   1Gi        RWO            standard       2m47s
mysql-instance-pvc          Bound    pvc-bcad5009-d14c-4ef2-aad4-993d6e337313   1Gi        RWO            standard       2m48s
```
    
## 5 Заполним базу данных
```
$ export MYSQLPOD=$(kubectl get pods -l app=mysql-instance -o jsonpath="{.items[*].metadata.name}") && \
  kubectl exec -it $MYSQLPOD -- mysql -u root -potuspassword -e "CREATE TABLE test ( id \
              smallint unsigned not null auto_increment, name varchar(20) not null, constraint \
              pk_example primary key (id) );" otus-database && \
  kubectl exec -it $MYSQLPOD -- mysql -potuspassword -e "INSERT INTO test ( id, name ) \
              VALUES ( null, 'some data' );" otus-database && \
  kubectl exec -it $MYSQLPOD -- mysql -potuspassword -e "INSERT INTO test ( id, name ) \
              VALUES ( null, 'some data-2' );" otus-database && \
  kubectl exec -it $MYSQLPOD -- mysql -potuspassword -e "select * from test;" otus-database
```

## 6 Посмотрим содержимое таблицы
```
$ kubectl exec -it $MYSQLPOD -- mysql -potuspassword -e "select * from test;" otus-database
+----+-------------+
| id | name        |
+----+-------------+
|  1 | some data   |
|  2 | some data-2 |
+----+-------------+
```
    
## 7 Удалим
```
$ kubectl delete mysqls.otus.homework mysql-instance

$ kubectl get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                               STORAGECLASS   REASON   AGE
backup-mysql-instance-pv                   1Gi        RWO            Retain           Available                                                               8m40s
pvc-5c8a55e8-e818-41fc-bfd1-aa35713ac42e   1Gi        RWO            Delete           Bound       default/backup-mysql-instance-pvc   standard                8m40s

$ kubectl get jobs.batch
NAME                         COMPLETIONS   DURATION   AGE
backup-mysql-instance-job    1/1           3s         48s
```
    
## 8 Cоздадим заново
```
$ kubectl apply -f deploy/cr.yml
$ export MYSQLPOD=$(kubectl get pods -l app=mysql-instance -o jsonpath="{.items[*].metadata.name}")
$ kubectl exec -it $MYSQLPOD -- mysql -potuspassword -e "select * from test;" otus-database

        +----+-------------+
        | id | name        |
        +----+-------------+
        |  1 | some data   |
        |  2 | some data-2 |
        +----+-------------+
```

## 9 Статус 
```
$ kubectl describe mysqls.otus.homework mysql-instance
Spec:
  Database:      otus-database
  Image:         mysql:5.7
  Password:      otuspassword
  storage_size:  1Gi
Status:
  mysql_on_create:
    Message:  mysql-instance created with restore-job
  update_object_password:
    Message:  mysql password changed
Events:
  Type    Reason    Age   From  Message
  ----    ------    ----  ----  -------
  Normal  Logging   3m2s  kopf  All handlers succeeded for creation.
  Normal  Logging   3m2s  kopf  Handler 'mysql_on_create' succeeded.
  Normal  Logging   57s   kopf  All handlers succeeded for update.
  Info    Password  57s   kopf  Update password
  Normal  Logging   57s   kopf  Handler 'update_object_password' succeeded.
```


## 10 Смена пароля
меняем пароль в cr.yaml
```
$ kubectl apply -f deploy/cr.yml
$ kubectl exec -it $MYSQLPOD -- mysql -potuspassword1 -e "select * from test;" otus-database
mysql: [Warning] Using a password on the command line interface can be insecure.
+----+-------------+
| id | name        |
+----+-------------+
|  1 | some data   |
|  2 | some data-2 |
+----+-------------+
```
