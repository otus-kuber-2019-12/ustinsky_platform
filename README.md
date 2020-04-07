# ustinsky_platform
ustinsky Platform repository

### Домашняя работа 1 ( [hw1 intro](docs/hw1.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-intro)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)

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

### Домашняя работа 2 ( [hw2 controlers](docs/hw2.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-controllers)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)

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

### Домашняя работа 3 ( [hw3 security](docs/hw3.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-security)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)
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

### Домашняя работа 5 ( [hw5 volumes](docs/hw5.md) ) [![Build Status](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform.svg?branch=kubernetes-volumes)](https://travis-ci.com/otus-kuber-2019-12/ustinsky_platform/)