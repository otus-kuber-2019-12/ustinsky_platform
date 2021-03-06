
# Домашняя работа 11 (Gitops)

## 0. ПОдготовка образов

### 0.1 Создаем проект
На gitlab.com создаем проект https://gitlab.com/ustinsky/microservices-demo

```
$ git clone https://github.com/GoogleCloudPlatform/microservices-demo
$ cd microservices-demo
$ git remote add gitlab git@gitlab.com:ustinsky/microservices-demo-1.git
$ git remote remove origin
$ git push gitlab master
```

### 0.2 Подготовить helm-chart-ы
```
$ grep -r avtandilko deploy/charts
$ sed -i 's/avtandilko/ustinsky/g' deploy/charts/*/values.yaml
```

### 0.3 Подготовить образы и залить на DockerHub 
```
$ export TAG=v0.0.1 
$ export REPO_PREFIX=ustinsky
$ bash ./hack/make-docker-images.sh
```


### 0.4 Подготовить кластер
```
# gcloud beta container clusters create "cluster" \
                        --machine-type "n1-standard-2" \
                        --disk-type "pd-standard" \
                        --disk-size "100" \
                        --metadata disable-legacy-endpoints=true \
                        --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
                        --num-nodes "4" \
                        --enable-stackdriver-kubernetes \
                        --enable-ip-alias \
                        --network "projects/otus-gitops/global/networks/default" \
                        --subnetwork "projects/otus-gitops/regions/europe-west2/subnetworks/default" \
                        --default-max-pods-per-node "110" \
                        --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing \
                        --enable-autoupgrade \
                        --enable-autorepair

$ gcloud beta container clusters create "mycluster" \
    --machine-type "n1-standard-2" \
    --num-nodes "4"
```

## 1. GitOps

### 1.1 Подготовка

Добавим репозиторий
```
$ helm repo add fluxcd https://charts.fluxcd.io && helm repo update
```

Установим CRD
```
$ kubectl apply -f https://raw.githubusercontent.com/fluxcd/helm-operator/master/deploy/crds.yaml
```

Установим Flux
```
$ kubectl create namespace flux
$ helm upgrade --install flux fluxcd/flux -f flux.values.yaml --namespace flux
```

Установим HelmOperator
```
$ helm upgrade --install helm-operator fluxcd/helm-operator -f helm-operator.values.yaml --namespace flux
```

Установим fluxctl (https://github.com/fluxcd/flux/releases)
```
$ wget https://github.com/fluxcd/flux/releases/download/1.19.0/fluxctl_linux_amd64
$ chmod +x fluxctl_linux_amd64
$ sudo cp fluxctl_linux_amd64 /usr/local/bin/fluxctl
$ fluxctl version
1.19.0
```

Добавим в Gitlab ключ fluxctl
```
$ fluxctl identity --k8s-fwd-ns flux
```

### 1.2 Добавим namespace
```
apiVersion: v1
kind: Namespace
metadata:
    name: microservices-demo
```

И выгрузим в gitlab

### 1.3 Проверка

Через некоторое время 
```
$ kubectl get ns
NAME                 STATUS   AGE
default              Active   60m
flux                 Active   25m
kube-node-lease      Active   60m
kube-public          Active   60m
kube-system          Active   60m
microservices-demo   Active   110s
production           Active   5m54s

$ kubectl logs flux-bf6b486bd-hmx7k -n flux | grep 'namespace/microservices-demo created'
ts=2020-06-15T07:56:28.925529816Z caller=sync.go:605 method=Sync cmd="kubectl apply -f -" took=297.196194ms err=null output="namespace/microservices-demo created\nnamespace/production unchanged\nhelmrelease.helm.fluxcd.io/adservice unchanged\nhelmrelease.helm.fluxcd.io/cartservice unchanged\nhelmrelease.helm.fluxcd.io/checkoutservice unchanged\nhelmrelease.helm.fluxcd.io/currencyservice unchanged\nhelmrelease.helm.fluxcd.io/emailservice unchanged\nhelmrelease.helm.fluxcd.io/frontend unchanged\nhelmrelease.helm.fluxcd.io/grafana-load-dashboards unchanged\nhelmrelease.helm.fluxcd.io/loadgenerator unchanged\nhelmrelease.helm.fluxcd.io/paymentservice unchanged\nhelmrelease.helm.fluxcd.io/productcatalogservice unchanged\nhelmrelease.helm.fluxcd.io/recommendationservice unchanged\nhelmrelease.helm.fluxcd.io/shippingservice unchanged"

$ kubectl get helmrelease -n microservices-demo
NAME       RELEASE    PHASE       STATUS     MESSAGE                                                                       AGE
frontend   frontend   Succeeded   deployed   Release was successful for Helm release 'frontend' in 'microservices-demo'.   6m57s
```

запустить: ``fluxctl --k8s-fwd-ns flux sync``

```
$ helm list -n microservices-demo
NAME            NAMESPACE               REVISION        UPDATED                                 STATUS          CHART           APP VERSION
frontend        microservices-demo      1               2020-06-15 10:54:51.853632236 +0000 UTC deployed        frontend-0.21.0 1.16.0
```

### 1.4 Обновляем 
Добавим в файл main.go
```
func myLexLog(msg string) {
	fmt.Printf(msg)
}
```

Пересоберем
```
$ docker build -t ustinsky/frontend:v0.0.2 .
$ docker push ustinsky/frontend:v0.0.2
```

Смотрим
``` 
$ helm list -n microservices-demo
NAME            NAMESPACE               REVISION        UPDATED                                 STATUS          CHART           APP VERSION
frontend        microservices-demo      2               2020-06-15 11:40:57.042834922 +0000 UTC deployed        frontend-0.21.0 1.16.0 

$ helm history frontend -n microservices-demo
REVISION        UPDATED                         STATUS          CHART           APP VERSION     DESCRIPTION     
1               Mon Jun 15 10:54:51 2020        superseded      frontend-0.21.0 1.16.0          Install complete
2               Mon Jun 15 11:40:57 2020        deployed        frontend-0.21.0 1.16.0          Upgrade complete

$ git diff 8eabe481..6c8024eb4
diff --git a/deploy/releases/frontend.yaml b/deploy/releases/frontend.yaml
index 759224e..358216e 100644
--- a/deploy/releases/frontend.yaml
+++ b/deploy/releases/frontend.yaml
@@ -18,4 +18,4 @@ spec:
   values:
     image:
       repository: ustinsky/frontend
-      tag: v0.0.2
+      tag: v0.0.1
```


файл: **deploy/releases/frontend.yaml**
```
---
apiVersion: helm.fluxcd.io/v1
kind: HelmRelease
metadata:
  name: frontend
  namespace: microservices-demo
  annotations:
    fluxcd.io/ignore: "false"
    fluxcd.io/automated: "true"
    flux.weave.works/tag.chart-image: semver:~v0.0
spec:
  releaseName: frontend
  helmVersion: v3
  chart:
    git: git@gitlab.com:ustinsky/microservices-demo-1.git
    ref: master
    path: deploy/charts/frontend
  values:
    image:
      repository: ustinsky/frontend
      tag: v0.0.2
```

### 1.5 Еще раз посмотрим
Заменим frontend на frontend-hipster в deployment chart-а frontend

Обновился релиз
```
$ helm list -n microservices-demo
NAME            NAMESPACE               REVISION        UPDATED                                 STATUS          CHART           APP VERSION
frontend        microservices-demo      3               2020-06-15 12:00:15.813776417 +0000 UTC deployed        frontend-0.21.0 1.16.0 

$ kubectl logs helm-operator-555dfffccb-9q9r9 -n flux | grep "hipster"
ts=2020-06-15T12:00:15.977132927Z caller=helm.go:69 component=helm version=v3 info="Created a new Deployment called \"frontend-hipster\" in microservices-demo\n" targetNamespace=microservices-demo release=frontend

$ kubectl get pods -n microservices-demo 
NAME                               READY   STATUS    RESTARTS   AGE
frontend-hipster-bc88d9898-56fkd   1/1     Running   0          7m39s
```

### 1.6 Разворачиваем остальные микросервисы
```
$ sed -i 's/avtandilko/ustinsky/g' deploy/releases/*

$ kubectl get pods -n microservices-demo 
NAME                                     READY   STATUS     RESTARTS   AGE
adservice-86c4899fcb-2sn6s               1/1     Running    0          104m
cartservice-54d954bdf9-j5z7k             1/1     Running    2          104m
cartservice-redis-master-0               1/1     Running    0          104m
checkoutservice-7f664dbc5d-98klb         1/1     Running    0          104m
currencyservice-78b589b9c4-qt7h8         1/1     Running    0          104m
emailservice-55584694f4-vj5q4            1/1     Running    0          104m
frontend-hipster-bc88d9898-56fkd         1/1     Running    0          173m
paymentservice-6f889fd874-stfkx          1/1     Running    0          104m
productcatalogservice-846756b974-b6s87   1/1     Running    0          104m
recommendationservice-58cb799b76-p4w8q   1/1     Running    0          110s
shippingservice-9c6bbf4b-gg88s           1/1     Running    0          104m

NAME                    NAMESPACE               REVISION        UPDATED                                 STATUS          CHART                        APP VERSION
adservice               microservices-demo      1               2020-06-15 13:09:36.877775973 +0000 UTC deployed        adservice-0.5.0              1.16.0     
cartservice             microservices-demo      1               2020-06-15 13:09:48.739784588 +0000 UTC deployed        cartservice-0.4.1            1.16.0     
checkoutservice         microservices-demo      1               2020-06-15 13:09:37.28582536 +0000 UTC  deployed        checkoutservice-0.4.0        1.16.0     
currencyservice         microservices-demo      1               2020-06-15 13:09:37.147861824 +0000 UTC deployed        currencyservice-0.4.0        1.16.0     
emailservice            microservices-demo      1               2020-06-15 13:09:38.161980721 +0000 UTC deployed        emailservice-0.4.0           1.16.0     
frontend                microservices-demo      3               2020-06-15 12:00:15.813776417 +0000 UTC deployed        frontend-0.21.0              1.16.0     
grafana-load-dashboards microservices-demo      1               2020-06-15 13:09:39.818061937 +0000 UTC deployed        grafana-load-dashboards-0.0.3           
loadgenerator           microservices-demo      1               2020-06-15 13:09:40.365743114 +0000 UTC deployed        loadgenerator-0.4.0          1.16.0     
paymentservice          microservices-demo      1               2020-06-15 13:09:41.83765471 +0000 UTC  deployed        paymentservice-0.3.0         1.16.0     
productcatalogservice   microservices-demo      1               2020-06-15 13:09:43.564580998 +0000 UTC deployed        productcatalogservice-0.3.0  1.16.0     
recommendationservice   microservices-demo      1               2020-06-15 13:09:44.589821076 +0000 UTC deployed        recommendationservice-0.3.0  1.16.0     
shippingservice         microservices-demo      1               2020-06-15 13:09:46.37801437 +0000 UTC  deployed        shippingservice-0.3.0        1.16.0
```

### 1.7 Полезные команды
```
# переменная окружения, указывающая на namespace, в который установлен flux
# (альтернатива ключу --k8s-fwd-ns <flux installation ns>)
$ export FLUX_FORWARD_NAMESPACE=flux 

# посмотреть все workloads, которые находятся в зоне видимости flux
$ fluxctl list-workloads -a 

# посмотреть все Docker образы, используемые в кластере (в namespace microservices-demo)
$ fluxctl list-images -n microservices-demo 

# включить/выключить автоматизацию управления workload
  fluxctl automate/deautomate  

# установить всем сервисам в workload microservices-demo:helmrelease/frontend 
# политику обновления образов из Registry на базе семантического версионирования c маской 0.1.*
$ fluxctl policy -w microservices-demo:helmrelease/frontend --tag-all='semver:~0.1' -

# Приндительно запустить синхронизацию состояния git-репозитория с кластером
$ fluxctl sync 

# принудительно инициировать сканирование Registry на предмет наличия свежих Docker образов
$ fluxctl release --workload=microservices-demo:helmrelease/frontend --update-all-images 
```

## 2. Flagger

### 2.1 Установка istio
Установим https://istio.io/latest/docs/setup/getting-started/
```
$ curl -L https://istio.io/downloadIstio | sh -
$ cd istio-1.6.2/bin/
$ sudo cp istioctl /usr/local/bin/
$ istioctl manifest apply --set profile=demo
```

### 2.2 Установка Flagger
```
$ helm repo add flagger https://flagger.app
$ kubectl apply -f https://raw.githubusercontent.com/weaveworks/flagger/master/artifacts/flagger/crd.yaml
$ helm upgrade --install flagger flagger/flagger \
    --namespace=istio-system \
    --set crd.create=false \
    --set meshProvider=istio \
    --set metricsServer=http://prometheus:9090
```

### 2.3 Istio sidecar injector 

Добавить в **microservice-ns.yaml**
```
apiVersion: v1
kind: Namespace
metadata:
    name: microservices-demo
    labels:
      istio-injection: enabled   
```

посмотрим
```
$ kubectl get ns microservices-demo --show-labels
NAME                 STATUS   AGE     LABELS
microservices-demo   Active   5h47m   fluxcd.io/sync-gc-mark=sha256.e8OOXlPsHLTYCYfbmO31mcfIboFIBylRO-ia8FYz1KE,istio-injection=enabled

$ kubectl delete pods --all -n microservices-demo

$ kubectl describe pod -l app=frontend -n microservices-demo
containers:
  ...
  istio-proxy:
    Container ID:  docker://c5ecc4de4679b3607134adfb060fbc83cf7075d60e755ff7106b8a7cb5f0caf0
    Image:         docker.io/istio/proxyv2:1.6.2
    Image ID:      docker-pullable://istio/proxyv2@sha256:ac25e39a130f5678bef302adea9e22163cd9d4737b0777e4e5e8353d916e223f
    Port:          15090/TCP
    Host Port:     0/TCP
    Args:
      proxy
      sidecar
      --domain
      $(POD_NAMESPACE).svc.cluster.local
      --serviceCluster
      frontend.$(POD_NAMESPACE)
      --proxyLogLevel=warning
      --proxyComponentLogLevel=misc:error
      --trust-domain=cluster.local
      --concurrency


```

### 2.4 Добавить VirtualService и Gateway
```
$ kubectl get gateway -n microservices-demo
NAME               AGE
frontend-gateway   68s

$ kubectl get svc istio-ingressgateway -n istio-system
NAME                   TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)                                                                      AGE
istio-ingressgateway   LoadBalancer   10.47.253.171   34.90.83.224   15020:31767/TCP,80:32389/TCP,443:30702/TCP,31400:32728/TCP,15443:31696/TCP   132m
```

### 2.5 Canary
```
$ kubectl get canary -n microservices-demo
NAME       STATUS         WEIGHT   LASTTRANSITIONTIME
frontend   Initializing   0        2020-06-15T18:05:51Z

$ kubectl get pods -n microservices-demo -l app=frontend-hipster-primary
NAME                                        READY   STATUS    RESTARTS   AGE
frontend-hipster-primary-57c4d7bc67-nnbhx   2/2     Running   0          27s
```

В файле я убрал метрики request-duration. В принципе на сайте istio.io указаны несколько метрик которые можно использовать. Но я не стал.
Для loadbalancer был выставлен publicIP.

Выкатываем новую версию и ждем. Через какое-то время
```
$ kubectl describe canary frontend -n microservices-demo
Events:
  Type     Reason  Age              From     Message
  ----     ------  ----             ----     -------
  Warning  Synced  13m              flagger  frontend-hipster-primary.microservices-demo not ready: waiting for rollout to finish: observed deployment generation less then desired generation
  Warning  Synced  13m              flagger  frontend-hipster-primary.microservices-demo not ready: waiting for rollout to finish: 0 of 1 updated replicas are available
  Normal   Synced  12m              flagger  Initialization done! frontend.microservices-demo
  Normal   Synced  10m              flagger  New revision detected! Scaling up frontend-hipster.microservices-demo
  Normal   Synced  10m              flagger  Starting canary analysis for frontend-hipster.microservices-demo
  Normal   Synced  10m              flagger  Advance frontend.microservices-demo canary weight 5
  Normal   Synced  9m30s            flagger  Advance frontend.microservices-demo canary weight 10
  Normal   Synced  9m               flagger  Advance frontend.microservices-demo canary weight 15
  Normal   Synced  8m30s            flagger  Advance frontend.microservices-demo canary weight 20
  Normal   Synced  8m               flagger  Advance frontend.microservices-demo canary weight 25
  Normal   Synced  7m30s            flagger  Advance frontend.microservices-demo canary weight 30
  Normal   Synced  6m (x3 over 7m)  flagger  (combined from similar events): Promotion completed! Scaling down frontend-hipster.microservices-demo

$ kubectl get canaries -n microservices-demo 
NAME       STATUS      WEIGHT   LASTTRANSITIONTIME
frontend   Succeeded   0        2020-06-15T22:44:37Z

$ kubectl get pods -n microservices-demo 
NAME                                        READY   STATUS    RESTARTS   AGE
adservice-86c4899fcb-trbkh                  2/2     Running   0          10m
cartservice-54d954bdf9-gd2dg                2/2     Running   2          10m
cartservice-redis-master-0                  2/2     Running   0          10m
checkoutservice-7f664dbc5d-d9bzl            2/2     Running   0          10m
currencyservice-78b589b9c4-j8vzh            2/2     Running   0          10m
emailservice-55584694f4-szh28               2/2     Running   0          10m
frontend-hipster-56b9ff5464-znkxt           2/2     Running   0          64s
frontend-hipster-primary-5bbf57d9cf-tx8mb   2/2     Running   0          10m
loadgenerator-5f89f6487d-6q2m5              2/2     Running   0          10m
paymentservice-6f889fd874-p5bnc             2/2     Running   0          10m
productcatalogservice-846756b974-cbrx5      2/2     Running   0          10m
recommendationservice-58cb799b76-rhnv4      2/2     Running   0          10m
shippingservice-9c6bbf4b-rrb8k              2/2     Running   0          10m
```








