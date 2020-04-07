#Домашняя работа 5 (kubernetes-volumes)
## 1. kind
### 1.1 Установка 
```
https://kind.sigs.k8s.io/docs/user/quick-start#installation
```

### 1.2 Создаем кластер
```
kind create cluster
export KUBECONFIG="$(kind get kubeconfig-path --name="kind")"
```
### 1.3 Создаем файл minio-statefulset.yaml
```
wget https://raw.githubusercontent.com/express42/otus-platform-snippets/master/Module-02/Kuberenetes-volumes/minio-statefulset.yaml

```

содержимое:
```
apiVersion: apps/v1
kind: StatefulSet
metadata:
  # This name uniquely identifies the StatefulSet
  name: minio
spec:
  serviceName: minio
  replicas: 1
  selector:
    matchLabels:
      app: minio # has to match .spec.template.metadata.labels
  template:
    metadata:
      labels:
        app: minio # has to match .spec.selector.matchLabels
    spec:
      containers:
      - name: minio
        env:
        - name: MINIO_ACCESS_KEY
          value: "minio"
        - name: MINIO_SECRET_KEY
          value: "minio123"
        image: minio/minio:RELEASE.2019-07-10T00-34-56Z
        args:
        - server
        - /data 
        ports:
        - containerPort: 9000
        # These volume mounts are persistent. Each pod in the PetSet
        # gets a volume mounted based on this field.
        volumeMounts:
        - name: data
          mountPath: /data
        # Liveness probe detects situations where MinIO server instance
        # is not working properly and needs restart. Kubernetes automatically
        # restarts the pods if liveness checks fail.
        livenessProbe:
          httpGet:
            path: /minio/health/live
            port: 9000
          initialDelaySeconds: 120
          periodSeconds: 20
  # These are converted to volume claims by the controller
  # and mounted at the paths mentioned above. 
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 10Gi
```

применим
```
kubectl apply -f minio-statefulset.yaml
```

### 1.4 Создаем файл minio-headless-service.yaml
Для того, чтобы наш StatefulSet был доступен изнутри кластера, создадим Headless Service
```
wget https://raw.githubusercontent.com/express42/otus-platform-snippets/master/Module-02/Kuberenetes-volumes/minio-headless-service.yaml
```

```
apiVersion: v1
kind: Service
metadata:
  name: minio
  labels:
    app: minio
spec:
  clusterIP: None
  ports:
    - port: 9000
      name: minio
  selector:
    app: minio
```

```
kubectl apply -f minio-headless-service.yaml
```

## 2. Проверка работы
### 2.1 Используя команды
```
$ kubectl get statefulsets
NAME    READY   AGE
minio   1/1     72s

$ kubectl get pods
NAME      READY   STATUS    RESTARTS   AGE
minio-0   1/1     Running   0          94s

$ kubectl get pvc
NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-minio-0   Bound    pvc-a879f00f-d314-4c6c-bc88-a66cc9d2de8a   10Gi       RWO            standard       111s

$ kubectl get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                  STORAGECLASS   REASON   AGE
pvc-a879f00f-d314-4c6c-bc88-a66cc9d2de8a   10Gi       RWO            Delete           Bound    default/data-minio-0   standard                2m27s


$ kubectl describe pv pvc-a879f00f-d314-4c6c-bc88-a66cc9d2de8a
Name:            pvc-a879f00f-d314-4c6c-bc88-a66cc9d2de8a
Labels:          <none>
Annotations:     hostPathProvisionerIdentity: 7dd58493-7915-11ea-9f86-0800277f955c
                 pv.kubernetes.io/provisioned-by: k8s.io/minikube-hostpath
Finalizers:      [kubernetes.io/pv-protection]
StorageClass:    standard
Status:          Bound
Claim:           default/data-minio-0
Reclaim Policy:  Delete
Access Modes:    RWO
VolumeMode:      Filesystem
Capacity:        10Gi
Node Affinity:   <none>
Message:         
Source:
    Type:          HostPath (bare host directory volume)
    Path:          /tmp/hostpath-provisioner/pvc-a879f00f-d314-4c6c-bc88-a66cc9d2de8a
    HostPathType:  
Events:            <none>
```
### 2.2 Используя minio/mc (https://github.com/minio/mc)

Создаем 2 контейнера
```
$ kubectl -it run minio-mc --image=ubuntu --generator=run-pod/v1 -- /bin/bash
$ kubectl -it run minio-mc2 --image=ubuntu --generator=run-pod/v1 -- /bin/bash
If you don't see a command prompt, try pressing enter.
root@minio-mc2:/#
```

Устанавливаем
```
$ apt update && apt install -y wget inetutils-ping && wget https://dl.min.io/client/mc/release/linux-amd64/mc && chmod +x mc
$ ./mc --help
$ ./mc config host add minio http://minio:9000 minio minio123
$ ./mc ls play
```

На одном контейнере создаем файл - копируем его как бакет - на другом читаем
```
mc1$ echo 'Privet !!!' > mytextfile.txt
mc1$ ./mc mb play/mybucket-lex
Bucket created successfully `play/mybucket-lex`.

mc1$ ./mc cp mytextfile.txt play/mybucket-lex
mytextfile.txt:              11 B / 11 B ┃▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓┃ 27 B/s 0s

mc2$ ./mc cat play/mybucket-lex/mytextfile.txt
Privet !!!
```


## 3 Прячем секреты

### 3.1 Создаем файл секретов ***minio-secret.yaml***

```
kind: Secret 
apiVersion: v1 
metadata:
  name: minio-secret
stringData:
  MINIO_ACCESS_KEY: minio
  MINIO_SECRET_KEY: minio123

```

### 3.2 Меняем файл ***minio-statefulset.yaml***

В файле заменим
```
        env:
        - name: MINIO_ACCESS_KEY
          value: "minio"
        - name: MINIO_SECRET_KEY
          value: "minio123"
```

на

```
        env:
        - name: MINIO_ACCESS_KEY
          valueFrom: 
            secretKeyRef:
              name: minio-secret
              key: MINIO_ACCESS_KEY
        - name: MINIO_SECRET_KEY
          valueFrom: 
            secretKeyRef:
              name: minio-secret
              key: MINIO_SECRET_KEY
```

в итоге получим:

```
apiVersion: apps/v1
kind: StatefulSet
metadata:
  # This name uniquely identifies the StatefulSet
  name: minio
spec:
  serviceName: minio
  replicas: 1
  selector:
    matchLabels:
      app: minio # has to match .spec.template.metadata.labels
  template:
    metadata:
      labels:
        app: minio # has to match .spec.selector.matchLabels
    spec:
      containers:
      - name: minio
        env:
        - name: MINIO_ACCESS_KEY
          valueFrom: 
            secretKeyRef:
              name: minio-secret
              key: MINIO_ACCESS_KEY
        - name: MINIO_SECRET_KEY
          valueFrom: 
            secretKeyRef:
              name: minio-secret
              key: MINIO_SECRET_KEY
        # - name: MINIO_ACCESS_KEY
        #   value: "minio"
        # - name: MINIO_SECRET_KEY
        #   value: "minio123"
        image: minio/minio:RELEASE.2019-07-10T00-34-56Z
        args:
        - server
        - /data 
        ports:
        - containerPort: 9000
        # These volume mounts are persistent. Each pod in the PetSet
        # gets a volume mounted based on this field.
        volumeMounts:
        - name: data
          mountPath: /data
        # Liveness probe detects situations where MinIO server instance
        # is not working properly and needs restart. Kubernetes automatically
        # restarts the pods if liveness checks fail.
        livenessProbe:
          httpGet:
            path: /minio/health/live
            port: 9000
          initialDelaySeconds: 120
          periodSeconds: 20
  # These are converted to volume claims by the controller
  # and mounted at the paths mentioned above.
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 10Gi
```

### 3.3 Применим
```bash
kubectl apply -f minio-secret.yaml
kubectl apply -f minio-statefulset.yaml
```