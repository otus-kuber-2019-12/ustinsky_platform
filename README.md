# ustinsky_platform
ustinsky Platform repository

## Домашняя работа 1 ( [hw1 intro](docs/hw1.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-intro)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)

### Разберитесь почему все pod в namespace kube-system восстановились после удаления.
kubelet запущен как сервис systemd. Он занимается процессом запуска pod-ов.
Если выполнить
~~~~ 
sudo systemctl stop kubelet; docker rm -f $(docker ps -a -q)
~~~~

то кластер не восстанавливается автоматически

для запуска кластера
~~~~
sudo systemctl start kubelet;
~~~~
после чего кластер запускает необходимые контейнеры

**core-dns** - реализован как Deployment с параметром replicas: 2. При его удалении ReplicaSet восстанавливает его работу

**kube-proxy** управляется и создается Daemonset.

**kube-apiserver**, **etcd**, **kube-controller-manager**, **kube-scheduler** - запускает kubelet ноды (/etc/kubernetes/manifests/)

### Создать pod
Создан самая простая программа http server на golang, взятая из учебника. Создан Dockerfile. Образ залит на DockerHub. 

Создан файл манифеста и запущен под. Пробрасываем подключение к поду и убеждаемся в его работоспособности
```
kubectl port-forward --address 0.0.0.0 pod/web 8000:8000
```

### Hipster shop
Создать файл описания пода можно с помощью команды
```
kubectl run frontend --image evgeniim/hipster-frontend --restart=Never --dry-run -o yaml > frontend-pod.yaml
```
Под не запускался из-за отсутсвия переменных окружений.

## Домашняя работа 2 ( [hw2 controlers](docs/hw2.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-controllers)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)

otus-kuber-2019-12/ustinsky_platform/

#### 1. Запустили kind 
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

#### 2. Создали ReplicaSet, Deployment для сервисов frontend, paymentservice

#### 3. **Почему обновление ReplicaSet не повлекло обновление запущенных pod ?**
***Ответ:*** Replicaset не умеет обновлять некоторые свой свойства - в частности шаблоны контейнеров (template). 
Шаблоны используются только при создании объекта ReplicaSet. 

#### 4. ***Поигрались*** с обновлениями и откатами новых версии приложений с использованием методов **Blue-Green** и **Reverse Rolling Update**

#### 5. Посмотрели на встроенные механизмы k8s управления готовностью пода к работе - **readinessProbe** и **livenessProbe**

#### 6. Нашли в интернете DaemonSet для ***node-exporter*** и развернули его на всех нодах кластера (мастер и воркер нодах).

#### 7. Разварачивание на master-нодах
Чтобы развернуть на мастер нодах нужно настроить параметр ***tolerations***

## Домашняя работа 3 ( [hw3 security](docs/hw3.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-security)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)
#### task01

1. Создан Service Account bob , дана ему роль admin в рамках всего кластера
2. Создать Service Account dave без доступа к кластеру

#### task02

1. Создан Namespace prometheus
2. Создан Service Account carol в namespace prometheus
3. Дан всем Service Account в Namespace prometheus возможность делать get , list , watch в отношении Pods всего кластера

### task03

1. Создан Namespace dev
2. Создан Service Account jane в Namespace dev
3. Дана jane роль admin в рамках Namespace dev
4. Создан Service Account ken в Namespace dev
5. Дана ken роль view в рамках Namespace dev

## Домашняя работа 4 ( [hw4 networks](docs/hw4.md) )
#### 1. Работа с тестовым веб-приложением
 - 1. Добавлен проверок Pod (ReadinessProbe, LivenessProbe)
 - 2. Создан объект Deployment
 - 3. Добавлен сервис в кластер (ClusterIP)
 - 4. Включен режима балансировки IPVS

#### 2. Доступ к приложению извне кластера
 - 1. Установлен MetaILB в Layer2 режиме
 - 2. Добавлен сервис LoadBalancer
 - 3. Установлен ingress-контроллер и прокси ingress-nginx
 - 4. Созданы правила Ingress

#### 3 Для запуска:
```
kubectl apply -f web-deploy.yaml

kubectl apply -f web-svc-cip.yaml

# меняем настройки minikube
kubectl --namespace kube-system edit configmap/kube-proxy (ищем KubeProxyConfig и меняем mode: "" => mode: "ipvs")
kubectl --namespace kube-system delete pod --selector='k8s-app=kube-proxy'

kubectl apply -f https://raw.githubusercontent.com/google/metallb/v0.8.0/manifests/metallb.yaml

kubectl apply -f metallb-config.yaml

kubectl apply -f web-svc-lb.yaml

# получаем IP
minikube ip 

ip route add 172.17.255.0/24 via <IP>

kubectl apply -f coredns-svc-lb.yaml

kubeclt apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.27.1/deploy/static/mandatory.yaml

kubectl apply -f nginx-lb.yaml

kubectl apply -f web-svc-headless.yaml

kubectl apply -f web-ingress.yaml
```

## Домашняя работа 5 ( [hw5 volumes](docs/hw5.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-volumes)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)

1. Развернули minio
2. Спрятали секреты в secrets

## Домашняя работа 8 ( [hw8 monitoring](docs/hw8.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-monitoring)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)

В работе выполнено:
  * Установили prometheus с помощью helm3
  * Создали тестовый сервер nginx
  * Зашли на Grafana и Prometheus и увидели метрики


## Домашняя работа 13 ( [hw13 storage](docs/hw13.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-storage)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)

### 1. Запуск

#### 1.1 Устанавливаем Kubernetes( вариант k1s )

  - `git clone https://github.com/maniaque/k1s.git`
  - `cd k1s/vagrant/single/`
  - `vagrant up`
  - `vagrant ssh -c 'cat /home/vagrant/.kube/config' > ~/.kube/config`


#### 1.2 Установить CSI Host Path Driver:

  - `git clone https://github.com/kubernetes-csi/csi-driver-host-path.git`
  - `bash deploy_snap`
  - `cd csi-driver-host-path/`
  - `git checkout 99036d47eab`
  - `deploy/kubernetes-1.17/deploy.sh`

#### 1.3 Запускаем

  - `kubectl apply -f hw/01-sc.yaml`
  - `kubectl apply -f hw/02-pvc.yaml`
  - `kubectl apply -f hw/03-pod.yaml`


### 2. ISCSI

Установили и поигрались с ISCSI

## Домашняя работа 14 ( [hw14 kubernetes-production-clusters](docs/hw14.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-production-clusters)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)

В работе выполнено:
  * Установили кластер k8s с помощью kubeadm
  * Обновили кластер до версии 18
  * Установили кластер с помошью kubespray

Файлы в папке kubernetes-production-clusters:
  * deployment.yml  - развертывание nginx
  * inventory.ini   - playbook для kuberspray с 1 мастер нодой и 3 воркер нодами
  * inventory2.ini  - playbook для kuberspray с 3 мастер нодами и 2 воркер нодами