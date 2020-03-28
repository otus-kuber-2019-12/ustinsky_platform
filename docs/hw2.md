# 1. Запустим kind

## 1.1 Развертываем кластер  
~~~~~~
kind create cluster --config kind-config.yaml
~~~~~~

Содержимое kind-config.yaml
~~~~~~
kind: Cluster
apiVersion: kind.sigs.k8s.io/v1alpha3
nodes:
- role: control-plane
- role: control-plane
- role: control-plane
- role: worker
- role: worker
- role: worker
~~~~~~

## 1.2 Проверяем
~~~~~~
kubectl get nodes
~~~~~~

выводит
~~~~~~
NAME                  STATUS   ROLES    AGE   VERSION
kind-control-plane    Ready    master   30m   v1.17.0
kind-control-plane2   Ready    master   29m   v1.17.0
kind-control-plane3   Ready    master   28m   v1.17.0
kind-worker           Ready    <none>   27m   v1.17.0
kind-worker2          Ready    <none>   27m   v1.17.0
kind-worker3          Ready    <none>   27m   v1.17.0
~~~~~~

# 2, ReplicaSet

## 2.1 Запускаем frontend
~~~~~~
kubectl apply -f frontend-replicaset.yaml
kubectl get pods -l app=frontend
~~~~~~

~~~~~~
NAME             READY   STATUS    RESTARTS   AGE
frontend-z8ng4   1/1     Running   0          3m7s
~~~~~~

содержимое файла frontend-replicaset.yaml
~~~~~~
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: server
        image: austinsky/hipster-frontend:v0.0.1
        env:
        - name: PRODUCT_CATALOG_SERVICE_ADDR
          value: "vasya"
        - name: CURRENCY_SERVICE_ADDR
          value: "petya"

        - name: CART_SERVICE_ADDR
          value: "vanya"
    
        - name: RECOMMENDATION_SERVICE_ADDR
          value: "zhenya"
    
        - name: SHIPPING_SERVICE_ADDR
          value: "vasya"
   
        - name: CHECKOUT_SERVICE_ADDR
          value: "check"
    
        - name: AD_SERVICE_ADDR
          value: "ImenaConchilis"
~~~~~~


## 2.2 Повышаем количество реплик
~~~~~~
kubectl scale replicaset frontend --replicas=3
~~~~~~

~~~~~~
NAME             READY   STATUS    RESTARTS   AGE
frontend-m9lr5   1/1     Running   0          3m13s
frontend-rgsx9   1/1     Running   0          3m13s
frontend-z8ng4   1/1     Running   0          7m24s
~~~~~~

~~~~~~
kubectl get rs frontend
~~~~~~

~~~~~~
NAME       DESIRED   CURRENT   READY   AGE
frontend   3         3         3       10m
~~~~~~

## 2.3 Проверим восстановление подов в случае удаления
~~~~~~
$ kubectl delete pods -l app=frontend | kubectl get pods -l app=frontend -w
frontend-m9lr5   1/1     Terminating   0          8m2s
frontend-rgsx9   1/1     Terminating   0          8m2s
frontend-z8ng4   1/1     Running       0          12m
frontend-z8ng4   1/1     Terminating   0          12m
frontend-q9m86   0/1     Pending       0          0s
frontend-q9m86   0/1     Pending       0          1s
frontend-qbdbb   0/1     Pending       0          1s
frontend-q9m86   0/1     ContainerCreating   0          2s
frontend-qbdbb   0/1     Pending             0          1s
frontend-jgh2d   0/1     Pending             0          0s
frontend-jgh2d   0/1     Pending             0          0s
frontend-z8ng4   0/1     Terminating         0          12m
frontend-rgsx9   0/1     Terminating         0          8m6s
frontend-jgh2d   0/1     ContainerCreating   0          1s
frontend-qbdbb   0/1     ContainerCreating   0          2s
frontend-m9lr5   0/1     Terminating         0          8m7s
frontend-m9lr5   0/1     Terminating         0          8m8s
frontend-m9lr5   0/1     Terminating         0          8m8s
frontend-q9m86   1/1     Running             0          6s
frontend-qbdbb   1/1     Running             0          5s
frontend-jgh2d   1/1     Running             0          5s
frontend-z8ng4   0/1     Terminating         0          12m
frontend-z8ng4   0/1     Terminating         0          12m
frontend-rgsx9   0/1     Terminating         0          8m17s
frontend-rgsx9   0/1     Terminating         0          8m18s
~~~~~~

~~~~~~
$ kubectl get rs frontend
NAME       DESIRED   CURRENT   READY   AGE
frontend   3         3         3       13m
~~~~~~

~~~~~~
$ kubectl get pods -l app=frontend
NAME             READY   STATUS    RESTARTS   AGE
frontend-jgh2d   1/1     Running   0          118s
frontend-q9m86   1/1     Running   0          2m
frontend-qbdbb   1/1     Running   0          119s
~~~~~~

## 2.4 Изменяем манифест - replica: 3
Поправим в манифесте реплики и переменные окружения. Переменные окружения берем из оригинала 
https://github.com/GoogleCloudPlatform/microservices-demo/blob/master/release/kubernetes-manifests.yaml

получилось:
~~~~~~
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: server
        image: austinsky/hipster-frontend:v0.0.1
        ports:
          - containerPort: 8080
        env:
          - name: PORT
            value: "8080"
          - name: PRODUCT_CATALOG_SERVICE_ADDR
            value: "productcatalogservice:3550"
          - name: CURRENCY_SERVICE_ADDR
            value: "currencyservice:7000"
          - name: CART_SERVICE_ADDR
            value: "cartservice:7070"
          - name: RECOMMENDATION_SERVICE_ADDR
            value: "recommendationservice:8080"
          - name: SHIPPING_SERVICE_ADDR
            value: "shippingservice:50051"
          - name: CHECKOUT_SERVICE_ADDR
            value: "checkoutservice:5050"
          - name: AD_SERVICE_ADDR
            value: "adservice:9555"
~~~~~~

проверим
~~~~~~
$ kubectl apply -f frontend-replicaset.yaml
replicaset.apps/frontend configured

$ kubectl get rs frontend
NAME       DESIRED   CURRENT   READY   AGE
frontend   3         3         3       33m

$ kubectl get pods -l app=frontend
NAME             READY   STATUS    RESTARTS   AGE
frontend-626g6   1/1     Running   0          37s
frontend-gmn8p   1/1     Running   0          37s
frontend-q9m86   1/1     Running   0          21m
~~~~~~

## 2.5 Изменим версию образа с 0.0.1 на 0.0.2
~~~~~~
$ kubectl apply -f frontend-replicaset.yaml 
replicaset.apps/frontend configured

$ kubectl apply -f frontend-replicaset.yaml | kubectl get pods -l app=frontend -w
NAME             READY   STATUS    RESTARTS   AGE
frontend-626g6   1/1     Running   0          37m
frontend-gmn8p   1/1     Running   0          37m
frontend-q9m86   1/1     Running   0          58m
~~~~~~

Образ указанный в ReplicaSet
~~~~~~
$ kubectl get replicaset frontend -o=jsonpath='{.spec.template.spec.containers[0].image}'
austinsky/hipster-frontend:v0.0.2
~~~~~~

Запущенный образ:
~~~~~~
$ kubectl get pods -l app=frontend -o=jsonpath='{.items[0:3].spec.containers[0].image}'
austinsky/hipster-frontend:v0.0.1 austinsky/hipster-frontend:v0.0.1 austinsky/hipster-frontend:v0.0.1
~~~~~~

## 2.6 Пересоздадим все
~~~~~~
$ kubectl delete rs/frontend
replicaset.apps "frontend" deleted

$ kubectl apply -f frontend-replicaset.yaml 
replicaset.apps/frontend created

$ kubectl get replicaset frontend -o=jsonpath='{.spec.template.spec.containers[0].image}'
austinsky/hipster-frontend:v0.0.2

$ kubectl get pods -l app=frontend -o=jsonpath='{.items[0:3].spec.containers[0].image}'
austinsky/hipster-frontend:v0.0.2 austinsky/hipster-frontend:v0.0.2 austinsky/hipster-frontend:v0.0.2
~~~~~~

## 2.7 Почему обновление ReplicaSet не повлекло обновление запущенных pod ?
Ответ: Replicaset не умеет обновлять некоторые свой свойства - в частности шаблоны контейнеров (template). 
Шаблоны используются только при создании объекта ReplicaSet. 

# 3. Deployment
## 3.1 Собираем paymentService
~~~~~~
$ cd microservices-demo/src/paymentservice

$ docker build .
...
Removing intermediate container 75043784c463
 ---> acc7bbbb5e3c
Successfully built acc7bbbb5e3c

$ docker tag acc7bbbb5e3c austinsky/paymentservice:v0.0.1
$ docker tag acc7bbbb5e3c austinsky/paymentservice:v0.0.2

$ docker push austinsky/paymentservice:v0.0.1
$ docker push austinsky/paymentservice:v0.0.2
~~~~~~

Пишем манифест:
~~~~~~
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: paymentservice
  labels:
    app: paymentservice
spec:
  replicas: 3
  selector:
    matchLabels:
      app: paymentservice
  template:
    metadata:
      labels:
        app: paymentservice
    spec:
      containers:
      - name: server
        image: austinsky/paymentservice:v0.0.1
        ports:
        - containerPort: 50051
        env:
        - name: PORT
          value: "50051"
        readinessProbe:
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:50051"]
        livenessProbe:
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:50051"]
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
~~~~~~

Применяем
~~~~~~
$ kubectl apply -f paymentservice-replicaset.yaml 
replicaset.apps/paymentservice created

$ kubectl get pod
NAME                   READY   STATUS    RESTARTS   AGE
frontend-f87xd         1/1     Running   0          2m23s
frontend-wmddv         1/1     Running   0          2m23s
frontend-z26r4         1/1     Running   0          2m23s
paymentservice-bqfll   1/1     Running   0          2m16s
paymentservice-jsnrj   1/1     Running   0          2m16s
paymentservice-n7gs2   1/1     Running   0          2m16s

$ kubectl delete -f paymentservice-replicaset.yaml
replicaset.apps "paymentservice" deleted

$ kubectl get pod
NAME                   READY   STATUS        RESTARTS   AGE
frontend-f87xd         1/1     Running       0          5m27s
frontend-wmddv         1/1     Running       0          5m27s
frontend-z26r4         1/1     Running       0          5m27s
paymentservice-jsnrj   0/1     Terminating   0          5m20s
~~~~~~

## 3.2 Создаем Deployment
Содержимое файла paymentservice-deployment.yaml
~~~~~~
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paymentservice
  labels:
    app: paymentservice
spec:
  replicas: 3
  selector:
    matchLabels:
      app: paymentservice
  template:
    metadata:
      labels:
        app: paymentservice
    spec:
      containers:
      - name: server
        image: austinsky/paymentservice:v0.0.1
        ports:
        - containerPort: 50051
        env:
        - name: PORT
          value: "50051"
        readinessProbe:
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:50051"]
        livenessProbe:
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:50051"]
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
~~~~~~

~~~~~~
$ kubectl get rs
NAME       DESIRED   CURRENT   READY   AGE
frontend   3         3         3       8m

$ kubectl apply -f paymentservice-deployment.yaml 
deployment.apps/paymentservice created

$ kubectl get deployment
NAME             READY   UP-TO-DATE   AVAILABLE   AGE
paymentservice   3/3     3            3           26s

$ kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
frontend-f87xd                    1/1     Running   0          9m35s
frontend-wmddv                    1/1     Running   0          9m35s
frontend-z26r4                    1/1     Running   0          9m35s
paymentservice-5fc894b54b-d6hxm   1/1     Running   0          52s
paymentservice-5fc894b54b-q26sr   1/1     Running   0          52s
paymentservice-5fc894b54b-x8gnm   1/1     Running   0          52s

$ kubectl get rs
NAME                        DESIRED   CURRENT   READY   AGE
frontend                    3         3         3       9m56s
paymentservice-5fc894b54b   3         3         3       73s
~~~~~~

## 3.3 Обновление Deployment
меняем austinsky/paymentservice:v0.0.1 на austinsky/paymentservice:v0.0.2
~~~~~~
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paymentservice
  labels:
    app: paymentservice
spec:
  replicas: 3
  selector:
    matchLabels:
      app: paymentservice
  template:
    metadata:
      labels:
        app: paymentservice
    spec:
      containers:
      - name: server
        image: austinsky/paymentservice:v0.0.2
        ports:
        - containerPort: 50051
        env:
        - name: PORT
          value: "50051"
        readinessProbe:
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:50051"]
        livenessProbe:
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:50051"]
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
~~~~~~

~~~~~~
$ kubectl apply -f paymentservice-deployment.yaml | kubectl get pods -l app=paymentservice -w
NAME                              READY   STATUS    RESTARTS   AGE
paymentservice-5fc894b54b-bjqcc   1/1     Running   0          4m4s
paymentservice-5fc894b54b-v5l9b   1/1     Running   0          4m4s
paymentservice-5fc894b54b-wqqqf   1/1     Running   0          4m4s
paymentservice-7b6665dcb7-rg2qp   0/1     Pending   0          0s
paymentservice-7b6665dcb7-rg2qp   0/1     Pending   0          1s
paymentservice-7b6665dcb7-rg2qp   0/1     ContainerCreating   0          1s
paymentservice-7b6665dcb7-rg2qp   0/1     Running             0          7s
paymentservice-7b6665dcb7-rg2qp   1/1     Running             0          20s
paymentservice-5fc894b54b-bjqcc   1/1     Terminating         0          4m26s
paymentservice-7b6665dcb7-sh22q   0/1     Pending             0          0s
paymentservice-7b6665dcb7-sh22q   0/1     Pending             0          0s
paymentservice-7b6665dcb7-sh22q   0/1     ContainerCreating   0          0s
paymentservice-7b6665dcb7-sh22q   0/1     Running             0          7s
paymentservice-7b6665dcb7-sh22q   1/1     Running             0          15s
paymentservice-5fc894b54b-v5l9b   1/1     Terminating         0          4m41s
paymentservice-7b6665dcb7-h6vfd   0/1     Pending             0          0s
paymentservice-7b6665dcb7-h6vfd   0/1     Pending             0          0s
paymentservice-7b6665dcb7-h6vfd   0/1     ContainerCreating   0          0s
paymentservice-7b6665dcb7-h6vfd   0/1     Running             0          6s
paymentservice-5fc894b54b-bjqcc   0/1     Terminating         0          4m57s
paymentservice-7b6665dcb7-h6vfd   1/1     Running             0          15s
paymentservice-5fc894b54b-wqqqf   1/1     Terminating         0          4m58s
paymentservice-5fc894b54b-bjqcc   0/1     Terminating         0          5m7s
paymentservice-5fc894b54b-bjqcc   0/1     Terminating         0          5m7s
paymentservice-5fc894b54b-v5l9b   0/1     Terminating         0          5m13s
paymentservice-5fc894b54b-v5l9b   0/1     Terminating         0          5m17s
paymentservice-5fc894b54b-v5l9b   0/1     Terminating         0          5m17s
paymentservice-5fc894b54b-wqqqf   0/1     Terminating         0          5m29s
paymentservice-5fc894b54b-wqqqf   0/1     Terminating         0          5m37s
paymentservice-5fc894b54b-wqqqf   0/1     Terminating         0          5m37s



$ kubectget pods
NAME                              READY   STATUS    RESTARTS   AGE
frontend-f87xd                    1/1     Running   0          17m
frontend-wmddv                    1/1     Running   0          17m
frontend-z26r4                    1/1     Running   0          17m
paymentservice-7b6665dcb7-h6vfd   1/1     Running   0          99s
paymentservice-7b6665dcb7-rg2qp   1/1     Running   0          2m16s
paymentservice-7b6665dcb7-sh22q   1/1     Running   0          115s

$ kubectl get rs
NAME                        DESIRED   CURRENT   READY   AGE
frontend                    3         3         3       20m
paymentservice-5fc894b54b   0         0         0       9m51s
paymentservice-7b6665dcb7   3         3         3       5m46s

$ kubectl get replicaset paymentservice-5fc894b54b -o=jsonpath='{.spec.template.spec.containers[0].image}'
austinsky/paymentservice:v0.0.1

$ kubectl get replicaset paymentservice-7b6665dcb7 -o=jsonpath='{.spec.template.spec.containers[0].image}'
austinsky/paymentservice:v0.0.2

$ kubectl get pods -l app=paymentservice -o=jsonpath='{.items[0:3].spec.containers[0].image}'
austinsky/paymentservice:v0.0.2 austinsky/paymentservice:v0.0.2 austinsky/paymentservice:v0.0.2

$ kubectl rollout history deployment paymentservice
deployment.apps/paymentservice 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
~~~~~~

## 3.4 Откатываемся назад
~~~~~~
$ kubectl rollout undo deployment paymentservice --to-revision=1 | kubectl get rs -l app=paymentservice -w
NAME                        DESIRED   CURRENT   READY   AGE
paymentservice-5fc894b54b   0         0         0       16m
paymentservice-7b6665dcb7   3         3         3       12m
paymentservice-5fc894b54b   0         0         0       16m
paymentservice-5fc894b54b   1         0         0       16m
paymentservice-5fc894b54b   1         0         0       16m
paymentservice-5fc894b54b   1         1         0       16m
paymentservice-5fc894b54b   1         1         1       16m
paymentservice-7b6665dcb7   2         3         3       12m
paymentservice-5fc894b54b   2         1         1       16m
paymentservice-7b6665dcb7   2         3         3       12m
paymentservice-7b6665dcb7   2         2         2       12m
paymentservice-5fc894b54b   2         1         1       16m
paymentservice-5fc894b54b   2         2         1       16m
paymentservice-5fc894b54b   2         2         2       17m
paymentservice-7b6665dcb7   1         2         2       13m
paymentservice-7b6665dcb7   1         2         2       13m
paymentservice-5fc894b54b   3         2         2       17m
paymentservice-7b6665dcb7   1         1         1       13m
paymentservice-5fc894b54b   3         2         2       17m
paymentservice-5fc894b54b   3         3         2       17m
paymentservice-5fc894b54b   3         3         3       17m
paymentservice-7b6665dcb7   0         1         1       13m
paymentservice-7b6665dcb7   0         1         1       13m
paymentservice-7b6665dcb7   0         0         0       13m

$ kubectl get rs
NAME                        DESIRED   CURRENT   READY   AGE
frontend                    3         3         3       29m
paymentservice-5fc894b54b   3         3         3       18m
paymentservice-7b6665dcb7   0         0         0       14m

$ kubectl get pods -l app=paymentservice -o=jsonpath='{.items[0:3].spec.containers[0].image}'
austinsky/paymentservice:v0.0.1 austinsky/paymentservice:v0.0.1 austinsky/paymentservice:v0.0.1
~~~~~~

## 3.5 Blue-green конфигурация
1. Развертывание трех новых pod
2. Удаление трех старых pod
~~~~~~
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 100%
      maxUnavailable: 0
~~~~~~

## 3.6 Конфигурация Reverse Rolling Update
1. Удаление одного старого pod
2. Создание одного нового pod
3. ...
~~~~~~
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 0
      maxUnavailable: 1
~~~~~~

# 4. Probes

## 4.1 Готовим манифест из https://github.com/GoogleCloudPlatform/microservices-demo/blob/master/kubernetes-manifests/frontend.yaml
~~~~~~
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
      annotations:
        sidecar.istio.io/rewriteAppHTTPProbers: "true"
    spec:
      containers:
        - name: server
          image: austinsky/hipster-frontend:v0.0.1
          ports:
          - containerPort: 8080
          readinessProbe:
            initialDelaySeconds: 10
            httpGet:
              path: "/_healthz"
              port: 8080
              httpHeaders:
              - name: "Cookie"
                value: "shop_session-id=x-readiness-probe"
          livenessProbe:
            initialDelaySeconds: 10
            httpGet:
              path: "/_healthz"
              port: 8080
              httpHeaders:
              - name: "Cookie"
                value: "shop_session-id=x-liveness-probe"
          env:
          - name: PORT
            value: "8080"
          - name: PRODUCT_CATALOG_SERVICE_ADDR
            value: "productcatalogservice:3550"
          - name: CURRENCY_SERVICE_ADDR
            value: "currencyservice:7000"
          - name: CART_SERVICE_ADDR
            value: "cartservice:7070"
          - name: RECOMMENDATION_SERVICE_ADDR
            value: "recommendationservice:8080"
          - name: SHIPPING_SERVICE_ADDR
            value: "shippingservice:50051"
          - name: CHECKOUT_SERVICE_ADDR
            value: "checkoutservice:5050"
          - name: AD_SERVICE_ADDR
            value: "adservice:9555"
          # - name: DISABLE_TRACING
          #   value: "1"
          # - name: DISABLE_PROFILER
          #   value: "1"
          # - name: JAEGER_SERVICE_ADDR
          #   value: "jaeger-collector:14268"
          resources:
            requests:
              cpu: 100m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
~~~~~~

Попробуем запустить
~~~~~~
$ kubectl apply -f frontend-deployment.yaml 
deployment.apps/frontend created

$ kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
frontend-5cb77d8dd4-4ghn7         1/1     Running   0          26m
frontend-5cb77d8dd4-kst2p         1/1     Running   0          25m
frontend-5cb77d8dd4-sgffx         1/1     Running   0          25m
paymentservice-7b6665dcb7-5rshv   1/1     Running   0          48m
paymentservice-7b6665dcb7-5xcqg   1/1     Running   0          47m
paymentservice-7b6665dcb7-bfhcx   1/1     Running   0          48m

$ kubectl describe pod/frontend-5cb77d8dd4-4ghn7
Name:         frontend-5cb77d8dd4-4ghn7
Namespace:    default
Priority:     0
Node:         kind-worker2/172.17.0.4
Start Time:   Sat, 28 Mar 2020 22:09:23 +0300
Labels:       app=frontend
              pod-template-hash=5cb77d8dd4
Annotations:  sidecar.istio.io/rewriteAppHTTPProbers: true
Status:       Running
IP:           10.244.4.11
IPs:
  IP:           10.244.4.11
Controlled By:  ReplicaSet/frontend-5cb77d8dd4
Containers:
  server:
    Container ID:   containerd://95547a68a51ae1d81edbcdd4abed285b8f3ff78e71ac00bd9384a74cbbe90661
    Image:          austinsky/hipster-frontend:v0.0.1
    Image ID:       docker.io/austinsky/hipster-frontend@sha256:ffeab7624ce47c6aa96d4d897c247fcca3620fb1aacf7bd9e3673e092cf78942
    Port:           8080/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Sat, 28 Mar 2020 22:09:28 +0300
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     200m
      memory:  128Mi
    Requests:
      cpu:      100m
      memory:   64Mi
    Liveness:   http-get http://:8080/_healthz delay=10s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:8080/_healthz delay=10s timeout=1s period=10s #success=1 #failure=3
    Environment:
      PORT:                          8080
      PRODUCT_CATALOG_SERVICE_ADDR:  productcatalogservice:3550
      CURRENCY_SERVICE_ADDR:         currencyservice:7000
      CART_SERVICE_ADDR:             cartservice:7070
      RECOMMENDATION_SERVICE_ADDR:   recommendationservice:8080
      SHIPPING_SERVICE_ADDR:         shippingservice:50051
      CHECKOUT_SERVICE_ADDR:         checkoutservice:5050
      AD_SERVICE_ADDR:               adservice:9555
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-b8fw5 (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             True 
  ContainersReady   True 
  PodScheduled      True 
Volumes:
  default-token-b8fw5:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  default-token-b8fw5
    Optional:    false
QoS Class:       Burstable
Node-Selectors:  <none>
Tolerations:     node.kubernetes.io/not-ready:NoExecute for 300s
                 node.kubernetes.io/unreachable:NoExecute for 300s
Events:
  Type    Reason     Age   From                   Message
  ----    ------     ----  ----                   -------
  Normal  Scheduled  29m   default-scheduler      Successfully assigned default/frontend-5cb77d8dd4-4ghn7 to kind-worker2
  Normal  Pulling    29m   kubelet, kind-worker2  Pulling image "austinsky/hipster-frontend:v0.0.1"
  Normal  Pulled     28m   kubelet, kind-worker2  Successfully pulled image "austinsky/hipster-frontend:v0.0.1"
  Normal  Created    28m   kubelet, kind-worker2  Created container server
  Normal  Started    28m   kubelet, kind-worker2  Started container server
~~~~~~

## 4.2 Имитируем отказ
~~~~~~
          readinessProbe:
            initialDelaySeconds: 10
            httpGet:
              path: "/_health"
              port: 8080
              httpHeaders:
              - name: "Cookie"
                value: "shop_session-id=x-readiness-probe"
~~~~~~

пробуем
~~~~~~
$ kubectl apply -f frontend-deployment.yaml 
deployment.apps/frontend configured

$ kubectl describe pod/frontend-f56fb9495-p4979
Name:         frontend-f56fb9495-p4979
Namespace:    default
Priority:     0
Node:         kind-worker2/172.17.0.4
Start Time:   Sat, 28 Mar 2020 22:41:52 +0300
Labels:       app=frontend
              pod-template-hash=f56fb9495
Annotations:  sidecar.istio.io/rewriteAppHTTPProbers: true
Status:       Running
IP:           10.244.4.12
IPs:
  IP:           10.244.4.12
Controlled By:  ReplicaSet/frontend-f56fb9495
Containers:
  server:
    Container ID:   containerd://778130fc46e04f891dfe3d4af273f99038d51a20b87bb4dcfefd4725380cec41
    Image:          austinsky/hipster-frontend:v0.0.2
    Image ID:       docker.io/austinsky/hipster-frontend@sha256:ffeab7624ce47c6aa96d4d897c247fcca3620fb1aacf7bd9e3673e092cf78942
    Port:           8080/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Sat, 28 Mar 2020 22:41:54 +0300
    Ready:          False
    Restart Count:  0
    Limits:
      cpu:     200m
      memory:  128Mi
    Requests:
      cpu:      100m
      memory:   64Mi
    Liveness:   http-get http://:8080/_healthz delay=10s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:8080/_health delay=10s timeout=1s period=10s #success=1 #failure=3
    Environment:
      PORT:                          8080
      PRODUCT_CATALOG_SERVICE_ADDR:  productcatalogservice:3550
      CURRENCY_SERVICE_ADDR:         currencyservice:7000
      CART_SERVICE_ADDR:             cartservice:7070
      RECOMMENDATION_SERVICE_ADDR:   recommendationservice:8080
      SHIPPING_SERVICE_ADDR:         shippingservice:50051
      CHECKOUT_SERVICE_ADDR:         checkoutservice:5050
      AD_SERVICE_ADDR:               adservice:9555
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-b8fw5 (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             False 
  ContainersReady   False 
  PodScheduled      True 
Volumes:
  default-token-b8fw5:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  default-token-b8fw5
    Optional:    false
QoS Class:       Burstable
Node-Selectors:  <none>
Tolerations:     node.kubernetes.io/not-ready:NoExecute for 300s
                 node.kubernetes.io/unreachable:NoExecute for 300s
Events:
  Type     Reason     Age               From                   Message
  ----     ------     ----              ----                   -------
  Normal   Scheduled  25s               default-scheduler      Successfully assigned default/frontend-f56fb9495-p4979 to kind-worker2
  Normal   Pulled     24s               kubelet, kind-worker2  Container image "austinsky/hipster-frontend:v0.0.2" already present on machine
  Normal   Created    23s               kubelet, kind-worker2  Created container server
  Normal   Started    23s               kubelet, kind-worker2  Started container server
  Warning  Unhealthy  1s (x2 over 11s)  kubelet, kind-worker2  Readiness probe failed: HTTP probe failed with statuscode: 404


$ kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
frontend-5cb77d8dd4-4ghn7         1/1     Running   0          37m
frontend-5cb77d8dd4-kst2p         1/1     Running   0          36m
frontend-5cb77d8dd4-sgffx         1/1     Running   0          36m
frontend-f56fb9495-p4979          0/1     Running   0          4m41s
paymentservice-7b6665dcb7-5rshv   1/1     Running   0          58m
paymentservice-7b6665dcb7-5xcqg   1/1     Running   0          58m
paymentservice-7b6665dcb7-bfhcx   1/1     Running   0          58m

$ kubectl rollout status deployment/frontend --timeout=60s
Waiting for deployment "frontend" rollout to finish: 1 out of 3 new replicas have been updated...
error: timed out waiting for the condition
lex@mebian:~/Документы/otus-kuber2/labs/lab2$ echo $?
1
~~~~~~

# 5. DaemonSet
## 5.1 Создаем манифест для node-exporter
Файл взят с https://raw.githubusercontent.com/coreos/kube-prometheus/master/manifests/node-exporter-daemonset.yaml
Из него убраны ***serviceAccountName: node-exporter***  и ***namespace: monitoring***
также ***labels*** были упрощены
~~~~~~
apiVersion: apps/v1
kind: DaemonSet
metadata:
  labels:
    app: node-exporter
  name: node-exporter
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      containers:
      - args:
        - --web.listen-address=127.0.0.1:9100
        - --path.procfs=/host/proc
        - --path.sysfs=/host/sys
        - --path.rootfs=/host/root
        - --collector.filesystem.ignored-mount-points=^/(dev|proc|sys|var/lib/docker/.+)($|/)
        - --collector.filesystem.ignored-fs-types=^(autofs|binfmt_misc|cgroup|configfs|debugfs|devpts|devtmpfs|fusectl|hugetlbfs|mqueue|overlay|proc|procfs|pstore|rpc_pipefs|securityfs|sysfs|tracefs)$
        image: quay.io/prometheus/node-exporter:v0.18.1
        name: node-exporter
        resources:
          limits:
            cpu: 250m
            memory: 180Mi
          requests:
            cpu: 102m
            memory: 180Mi
        volumeMounts:
        - mountPath: /host/proc
          name: proc
          readOnly: false
        - mountPath: /host/sys
          name: sys
          readOnly: false
        - mountPath: /host/root
          mountPropagation: HostToContainer
          name: root
          readOnly: true
      - args:
        - --logtostderr
        - --secure-listen-address=[$(IP)]:9100
        - --tls-cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_RSA_WITH_AES_128_CBC_SHA256,TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256,TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256
        - --upstream=http://127.0.0.1:9100/
        env:
        - name: IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        image: quay.io/coreos/kube-rbac-proxy:v0.4.1
        name: kube-rbac-proxy
        ports:
        - containerPort: 9100
          hostPort: 9100
          name: https
        resources:
          limits:
            cpu: 20m
            memory: 40Mi
          requests:
            cpu: 10m
            memory: 20Mi
      hostNetwork: true
      hostPID: true
      nodeSelector:
        kubernetes.io/os: linux
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
      # serviceAccountName: node-exporter
      # tolerations:
      # - operator: Exists
      volumes:
      - hostPath:
          path: /proc
        name: proc
      - hostPath:
          path: /sys
        name: sys
      - hostPath:
          path: /
        name: root
~~~~~~


## 5.2 Разворачиваем
~~~~~~
$ kubectl apply -f node-exporter-daemonset.yaml

$ kubectl get pods -o wide | grep node-exporter
node-exporter-7nf74               2/2     Running   0          4m57s   172.17.0.3    kind-control-plane3   <none>           <none>
node-exporter-dbdmq               2/2     Running   0          4m57s   172.17.0.8    kind-control-plane2   <none>           <none>
node-exporter-dkvrw               2/2     Running   0          4m57s   172.17.0.6    kind-control-plane    <none>           <none>
node-exporter-h4hxr               2/2     Running   0          4m57s   172.17.0.5    kind-worker3          <none>           <none>
node-exporter-kqq24               2/2     Running   0          4m57s   172.17.0.7    kind-worker           <none>           <none>
node-exporter-q8lvl               2/2     Running   0          4m57s   172.17.0.4    kind-worker2          <none>           <none>
~~~~~~

## 5.3 Проверяем 
kubectl port-forward <имя любого pod в DaemonSet> 9100:9100
~~~~~~
$ kubectl port-forward node-exporter-7nf74 9100:9100
Forwarding from 127.0.0.1:9100 -> 9100
Forwarding from [::1]:9100 -> 9100

$ curl localhost:9100/metrics
...
node_cpu_seconds_total{cpu="0",mode="nice"} 3.31
node_cpu_seconds_total{cpu="0",mode="softirq"} 118.42
node_cpu_seconds_total{cpu="0",mode="steal"} 0
node_cpu_seconds_total{cpu="0",mode="system"} 1098.66
node_cpu_seconds_total{cpu="0",mode="user"} 1961.27
node_cpu_seconds_total{cpu="1",mode="idle"} 5922.84
node_cpu_seconds_total{cpu="1",mode="iowait"} 1508.52
node_cpu_seconds_total{cpu="1",mode="irq"} 0
node_cpu_seconds_total{cpu="1",mode="nice"} 3.22
node_cpu_seconds_total{cpu="1",mode="softirq"} 79.66
node_cpu_seconds_total{cpu="1",mode="steal"} 0
node_cpu_seconds_total{cpu="1",mode="system"} 1052.7
node_cpu_seconds_total{cpu="1",mode="user"} 1859.48
node_cpu_seconds_total{cpu="2",mode="idle"} 5879.67
node_cpu_seconds_total{cpu="2",mode="iowait"} 1398.8
node_cpu_seconds_total{cpu="2",mode="irq"} 0
...
~~~~~~



## 5.4 Разварачиваем на master-нодах
В моем случае все работало без правки. Скачанный с сайта файл уже имел необходимые настройки для разворачивания 
на master нодах.

~~~~~~
$ kubectl get pods -o wide | grep node-exporter
node-exporter-7nf74               2/2     Running   0          4m57s   172.17.0.3    kind-control-plane3   <none>           <none>
node-exporter-dbdmq               2/2     Running   0          4m57s   172.17.0.8    kind-control-plane2   <none>           <none>
node-exporter-dkvrw               2/2     Running   0          4m57s   172.17.0.6    kind-control-plane    <none>           <none>
node-exporter-h4hxr               2/2     Running   0          4m57s   172.17.0.5    kind-worker3          <none>           <none>
node-exporter-kqq24               2/2     Running   0          4m57s   172.17.0.7    kind-worker           <none>           <none>
node-exporter-q8lvl               2/2     Running   0          4m57s   172.17.0.4    kind-worker2          <none>           <none>
~~~~~~

Если у вас не так, то чтобы развернуть на мастер нодах нужно настроить параметр ***tolerations***

~~~~~~
tolerations:
- operator: Exists
~~~~~~

или

~~~~~~
tolerations:
  - key: "node-role.kubernetes.io/master"
    effect: NoSchedule
    operator: "Exists"
~~~~~~