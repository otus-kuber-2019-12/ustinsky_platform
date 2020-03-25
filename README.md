# ustinsky_platform
ustinsky Platform repository

### Домашняя работа 1 ( [hw1 intro](docs/hw1.md) )

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