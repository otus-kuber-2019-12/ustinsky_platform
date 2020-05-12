# Домашняя работа 4 (kuber-network)
    



## 1. Работа с тестовым веб-приложением
### 1.1. Добавление проверок Pod
#### 1.1.1 Добавить в описание пода
```
spec:                                                   # Описание Pod
  containers:                                           # Описание контейнеров внутри Pod
  - name: web                                           # Название контейнера
    image: austinsky/example-go-httpd-alpine:v0.0.1
    readinessProbe:
        httpGet:
            path: /index.html
            port: 80
```

#### 1.1.2 Запустить под командой 
```
$ kubectl apply -f web-pod.yaml
pod/web created
```

#### 1.1.3 Проверяем запуск
```
$ kubectl get pod/web
NAME   READY   STATUS    RESTARTS   AGE
web    0/1     Running   0          96s
```
под не прошел проверку

#### 1.1.4 Смотрим события запуска
```
$ kubectl describe pod/web
Events:
  Type     Reason     Age                   From               Message
  ----     ------     ----                  ----               -------
  Normal   Scheduled  5m32s                 default-scheduler  Successfully assigned default/web to minikube
  Normal   Pulling    5m31s                 kubelet, minikube  Pulling image "busybox:1.31.0"
  Normal   Pulled     5m27s                 kubelet, minikube  Successfully pulled image "busybox:1.31.0"
  Normal   Created    5m27s                 kubelet, minikube  Created container initialize-index-htnl
  Normal   Started    5m27s                 kubelet, minikube  Started container initialize-index-htnl
  Normal   Pulling    5m26s                 kubelet, minikube  Pulling image "austinsky/example-go-httpd-alpine:v0.0.1"
  Normal   Pulled     4m48s                 kubelet, minikube  Successfully pulled image "austinsky/example-go-httpd-alpine:v0.0.1"
  Normal   Created    4m47s                 kubelet, minikube  Created container web
  Normal   Started    4m47s                 kubelet, minikube  Started container web
  Warning  Unhealthy  27s (x26 over 4m37s)  kubelet, minikube  Readiness probe failed: Get http://172.17.0.4:80/index.html: dial tcp 172.17.0.4:80: connect: connection refused
```

#### 1.1.5 Исправим 80 => 8000
```
spec:                                                   # Описание Pod
  containers:                                           # Описание контейнеров внутри Pod
  - name: web                                           # Название контейнера
    image: austinsky/example-go-httpd-alpine:v0.0.1     # Образ из которого создается контейнер
    readinessProbe:
      httpGet:
        path: /index.html
        port: 8000
```


```
$ kubectl get pod/web
NAME   READY   STATUS    RESTARTS   AGE
web    1/1     Running   0          7s
```
            
#### 1.1.6 Добавим liveness проверку
```
                livenessProbe:
                    tcpSocket: { port: 8000 }
```

#### 1.1.7 Вопрос
1. ***Почему следующая конфигурация валидна, но не имеет смысла?***
```
                    livenessProbe:
                        exec:
                            command:
                                - 'sh'
                                - '-c'
                                - 'ps aux | grep my_web_server_process'
```

Ответ:
```
В команде надо еще убрать вывод самой команды grep. 'ps aux | grep my_web_server_process | grep -v grep'
И даже в этом случае наличие процесса в списке процессов не гарантирует его корректную работу. Процесс может подвиснуть, 
переити в deadlock. Тогда в списке процессов он будет, проверку пройдет, но работать не будет. 
```
                
2.  ***Бывают ли ситуации, когда она все-таки имеет смысл?***

Ответ:
```
Возможно это используется для каких то задач, которые конечны (процесс завершиться после выполнения какой либо задачи). 
Далее для того чтобы отреагировала диагностика пода и убрала контейнер с завершенным процессом. Хотя для этого есть Job.

Другой вариант - это при развертывании убедиться что процесс запустился. Возможно процесс не сразу запускается, а еще есть 
какие либо подготовительные операции после чего запускается процесс
И в ходе развертывания нужно подождать когда он запуститься(от него  что-то зависит) и когда он запустился - продолжать
развертывание. Например можно использовать в ходе unit тестирования своих манифестов. Кластер kind развертывает инфраструктуру, далее мы ждем
когда все запуститься и начинаем тестировать инфраструктуру тестами. И чтобы понять что все что нам нужно уже работает - можно принудительно повесить такие livenessProbe или readinessProbe. Как они отработают - начинать проверку. 
```

### 1.2. Создание объекта Deployment
#### 1.2.1 Создаем файл web-deploy.yaml
``` 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web                 # Название нашего объекта Deployment
spec:
  replicas: 3               # Начнем с одного пода
  selector:                 # Укажем, какие поды относятся к нашему Deployment:
    matchLabels:            # - это поды с меткой
      app: web              # app и ее значением web
#  strategy:
#    type: RollingUpdate
#    rollingUpdate:
#      maxUnavailable: 0
#      maxSurge: 1%
  template:                 # Теперь зададим шаблон конфигурации пода
    metadata:
      name: web                                             # Название Pod
      labels:                                               # Метки в формате key: value
        app: web
    spec:                                                   # Описание Pod
      containers:                                           # Описание контейнеров внутри Pod
      - name: web                                           # Название контейнера
        image: austinsky/example-go-httpd-alpine:v0.0.1     # Образ из которого создается контейнер
        readinessProbe:
          httpGet:
            path: /index.html
            port: 8000
        livenessProbe:
          tcpSocket: { port: 8000 }
        volumeMounts:
        - name: app
          mountPath: /app
      initContainers:
      - name: initialize-index-htnl
        image: busybox:1.31.0
        command: ['sh', '-c', 'wget -O- https://raw.githubusercontent.com/express42/otus-platform-snippets/master/Module-02/Introduction-to-Kubernetes/wget.sh | sh']
        volumeMounts:
        - name: app
          mountPath: /app
      volumes:
      - name: app
        emptyDir: {}
```

#### 1.2.2 Удаляем старый под
```
$ kubectl delete pod/web --grace-period=0 --force
warning: Immediate deletion does not wait for confirmation that the running resource has been terminated. The resource may continue to run on the cluster indefinitely.
pod "web" force deleted

$ kubectl get pod/web
Error from server (NotFound): pods "web" not found
```
            
#### 1.2.3 Применяем Deployment
```
$ kubectl apply -f web-deploy.yaml
deployment.apps/web created
```

#### 1.2.4 Посмотрим что получилось
```
$ kubectl describe deployment web

Name:                   web
Namespace:              default
CreationTimestamp:      Mon, 11 May 2020 21:47:54 +0300
Labels:                 <none>
Annotations:            deployment.kubernetes.io/revision: 1
                        kubectl.kubernetes.io/last-applied-configuration:
                          {"apiVersion":"apps/v1","kind":"Deployment","metadata":{"annotations":{},"name":"web","namespace":"default"},"spec":{"replicas":3,"selecto...
Selector:               app=web
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1% max surge
Pod Template:
  Labels:  app=web
  Init Containers:
   initialize-index-htnl:
    Image:      busybox:1.31.0
    Port:       <none>
    Host Port:  <none>
    Command:
      sh
      -c
      wget -O- https://raw.githubusercontent.com/express42/otus-platform-snippets/master/Module-02/Introduction-to-Kubernetes/wget.sh | sh
    Environment:  <none>
    Mounts:
      /app from app (rw)
  Containers:
   web:
    Image:        austinsky/example-go-httpd-alpine:v0.0.1
    Port:         <none>
    Host Port:    <none>
    Liveness:     tcp-socket :8000 delay=0s timeout=1s period=10s #success=1 #failure=3
    Readiness:    http-get http://:8000/index.html delay=0s timeout=1s period=10s #success=1 #failure=3
    Environment:  <none>
    Mounts:
      /app from app (rw)
  Volumes:
   app:
    Type:       EmptyDir (a temporary directory that shares a pod's lifetime)
    Medium:     
    SizeLimit:  <unset>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   web-7597c86f94 (3/3 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  33s   deployment-controller  Scaled up replica set web-7597c86f94 to 3
```

#### 1.2.5 Добавляем стратегию
```
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 100%
```

#### 1.2.6 Поиграться с вариантами maxUnavailable, maxSurge
В ДЗ 2 мы игрались с MaxSurge и maxUnavailable
- maxSurge        - сколько подов нужно добавить к общему количеству
- maxUnavailable  - сколько подов может быть недоступно по отношению к общему количеству указаному в replicas Deployment

Конфигурация 0%/0% - недопустимая
```
$ kubectl apply -f web-deploy.yaml
The Deployment "web" is invalid: spec.strategy.rollingUpdate.maxUnavailable: Invalid value: intstr.IntOrString{Type:0, IntVal:0, StrVal:""}: may not be 0 when `maxSurge` is 0
```


#### 1.2.7 Blue-green конфигурация
1. Развертывание трех новых pod
2. Удаление трех старых pod
~~~~~~
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 100%
      maxUnavailable: 0
~~~~~~

```
$ kubectl get pods
NAME                   READY   STATUS     RESTARTS   AGE
web-7bbf96bdcf-6hc28   0/1     Init:0/1   0          2s
web-7bbf96bdcf-pv6nt   0/1     Init:0/1   0          2s
web-7bbf96bdcf-rp6vw   0/1     Init:0/1   0          3s
web-84d857c57b-f6d6r   1/1     Running    0          2m24s
web-84d857c57b-jfvxp   1/1     Running    0          2m24s
web-84d857c57b-lhl8v   1/1     Running    0          2m24s
$ kubectl get pods
NAME                   READY   STATUS        RESTARTS   AGE
web-7bbf96bdcf-6hc28   1/1     Running       0          9s
web-7bbf96bdcf-pv6nt   1/1     Running       0          9s
web-7bbf96bdcf-rp6vw   1/1     Running       0          10s
web-84d857c57b-jfvxp   0/1     Terminating   0          2m31s
web-84d857c57b-lhl8v   0/1     Terminating   0          2m31s
```

#### 1.2.8 Конфигурация Reverse Rolling Update
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

```
$ kubectl get pods
NAME                   READY   STATUS        RESTARTS   AGE
web-7bbf96bdcf-6hc28   0/1     Terminating   0          2m35s
web-7bbf96bdcf-pv6nt   1/1     Running       0          2m35s
web-7bbf96bdcf-rp6vw   1/1     Running       0          2m36s
web-84d857c57b-flcqn   0/1     Init:0/1      0          2s

$ kubectl get pods
NAME                   READY   STATUS        RESTARTS   AGE
web-7bbf96bdcf-pv6nt   0/1     Terminating   0          2m43s
web-84d857c57b-flcqn   1/1     Running       0          10s
web-84d857c57b-jc6vq   0/1     Init:0/1      0          2s
web-84d857c57b-x88cb   1/1     Running       0          6s

$ kubectl get pods
NAME                   READY   STATUS    RESTARTS   AGE
web-84d857c57b-flcqn   1/1     Running   0          24s
web-84d857c57b-jc6vq   1/1     Running   0          16s
web-84d857c57b-x88cb   1/1     Running   0          20s
```

```
$ kubectl get events --watch
0s          Normal    Started             pod/web-7597c86f94-kxnrw    Started container initialize-index-htnl
0s          Normal    Pulled              pod/web-7597c86f94-kxnrw    Container image "austinsky/example-go-httpd-alpine:v0.0.1" already present on machine
0s          Normal    Created             pod/web-7597c86f94-kxnrw    Created container web
0s          Normal    Started             pod/web-7597c86f94-kxnrw    Started container web
0s          Normal    ScalingReplicaSet   deployment/web              (combined from similar events): Scaled down replica set web-84d857c57b to 1
0s          Normal    Killing             pod/web-84d857c57b-x88cb    Stopping container web
0s          Normal    SuccessfulDelete    replicaset/web-84d857c57b   Deleted pod: web-84d857c57b-x88cb
0s          Normal    ScalingReplicaSet   deployment/web              (combined from similar events): Scaled up replica set web-7597c86f94 to 2
0s          Normal    SuccessfulCreate    replicaset/web-7597c86f94   Created pod: web-7597c86f94-wx9vq
0s          Normal    Scheduled           pod/web-7597c86f94-wx9vq    Successfully assigned default/web-7597c86f94-wx9vq to minikube
0s          Normal    Pulled              pod/web-7597c86f94-wx9vq    Container image "busybox:1.31.0" already present on machine
0s          Normal    Created             pod/web-7597c86f94-wx9vq    Created container initialize-index-htnl
0s          Normal    Started             pod/web-7597c86f94-wx9vq    Started container initialize-index-htnl
0s          Normal    Pulled              pod/web-7597c86f94-wx9vq    Container image "austinsky/example-go-httpd-alpine:v0.0.1" already present on machine
0s          Normal    Created             pod/web-7597c86f94-wx9vq    Created container web
0s          Normal    Started             pod/web-7597c86f94-wx9vq    Started container web
0s          Normal    ScalingReplicaSet   deployment/web              (combined from similar events): Scaled down replica set web-84d857c57b to 0
0s          Normal    Killing             pod/web-84d857c57b-flcqn    Stopping container web
0s          Normal    SuccessfulDelete    replicaset/web-84d857c57b   Deleted pod: web-84d857c57b-flcqn
1s          Normal    Scheduled           pod/web-7597c86f94-g5tgr    Successfully assigned default/web-7597c86f94-g5tgr to minikube
1s          Normal    SuccessfulCreate    replicaset/web-7597c86f94   Created pod: web-7597c86f94-g5tgr
1s          Normal    ScalingReplicaSet   deployment/web              (combined from similar events): Scaled up replica set web-7597c86f94 to 3
0s          Normal    Pulled              pod/web-7597c86f94-g5tgr    Container image "busybox:1.31.0" already present on machine
0s          Normal    Created             pod/web-7597c86f94-g5tgr    Created container initialize-index-htnl
0s          Normal    Started             pod/web-7597c86f94-g5tgr    Started container initialize-index-htnl
0s          Normal    Pulled              pod/web-7597c86f94-g5tgr    Container image "austinsky/example-go-httpd-alpine:v0.0.1" already present on machine
0s          Normal    Created             pod/web-7597c86f94-g5tgr    Created container web
0s          Normal    Started             pod/web-7597c86f94-g5tgr    Started container web
```

#### 1.2.9 Конфигурация 100%/100%
1. Удаляем все старые поды
2. Создаем все новые поды

```
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 100%
      maxSurge: 100%
```

пробуем
```
$ kubectl get pods
NAME                   READY   STATUS        RESTARTS   AGE
web-7bbf96bdcf-57xsd   0/1     Init:0/1      0          2s
web-7bbf96bdcf-8zqrl   0/1     Init:0/1      0          3s
web-7bbf96bdcf-xgm4j   0/1     Init:0/1      0          2s
web-84d857c57b-j6tb5   1/1     Terminating   0          6m10s
web-84d857c57b-rbjdh   1/1     Terminating   0          6m10s
web-84d857c57b-rj7rh   1/1     Terminating   0          6m10s

$ kubectl get pods
NAME                   READY   STATUS    RESTARTS   AGE
web-7bbf96bdcf-57xsd   1/1     Running   0          15s
web-7bbf96bdcf-8zqrl   1/1     Running   0          16s
web-7bbf96bdcf-xgm4j   1/1     Running   0          15s
```

### 1.3. Добавление сервисов в кластер (ClusterIP)
#### 1.3.1 Создаем сервис web-svc-cip.yaml
```
apiVersion: v1
kind: Service
metadata:
  name: web-svc-cip
spec:
  selector:
    app: web
  type: ClusterIP
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

#### 1.3.2 Применяем
```
$ kubectl apply -f web-svc-cip.yaml
```

#### 1.3.3 Проверяем
```
$ kubectl get services
NAME          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
kubernetes    ClusterIP   10.96.0.1      <none>        443/TCP   4h33m
web-svc-cip   ClusterIP   10.106.8.233   <none>        80/TCP    7m31s
```

#### 1.3.4 Проверяем цепочку
```
$ minikube ssh

$ curl http://<CLUSTER-IP>/index.html
$ curl -v 10.106.8.233/
...<html>...

$ ping <CLUSTER-IP> 
<пинга нет>

$ arp -an
$ ip addr show
<нигде нет ClusterIP>

$ iptables --list -nv -t nat
...
Chain OUTPUT (policy ACCEPT 20 packets, 1200 bytes)
...
20535 1239K KUBE-SERVICES  all  --  *      *       0.0.0.0/0            0.0.0.0/0            /* kubernetes service portals */
...

Chain KUBE-SERVICES (2 references)
...
 0     0 KUBE-SVC-WKCOG6KH24K26XRJ  tcp  --  *      *       0.0.0.0/0            10.106.8.233         /* default/web-svc-cip: cluster IP */ tcp dpt:80
...

Chain KUBE-SVC-WKCOG6KH24K26XRJ (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 KUBE-SEP-4EHRVUY3IKVUBA4M  all  --  *      *       0.0.0.0/0            0.0.0.0/0            statistic mode random probability 0.33332999982
    0     0 KUBE-SEP-S353CMO5VXPY3Z3E  all  --  *      *       0.0.0.0/0            0.0.0.0/0            statistic mode random probability 0.50000000000
    0     0 KUBE-SEP-3CEPG7JTIQEKQKXJ  all  --  *      *       0.0.0.0/0            0.0.0.0/0  

Chain PREROUTING (policy ACCEPT 0 packets, 0 bytes)
...
Chain KUBE-SEP-3CEPG7JTIQEKQKXJ (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 KUBE-MARK-MASQ  all  --  *      *       172.17.0.6           0.0.0.0/0           
    0     0 DNAT       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp to:172.17.0.6:8000

Chain KUBE-SEP-4EHRVUY3IKVUBA4M (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 KUBE-MARK-MASQ  all  --  *      *       172.17.0.4           0.0.0.0/0           
    0     0 DNAT       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp to:172.17.0.4:8000

Chain KUBE-SEP-S353CMO5VXPY3Z3E (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 KUBE-MARK-MASQ  all  --  *      *       172.17.0.5           0.0.0.0/0           
    0     0 DNAT       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp to:172.17.0.5:8000

...

```

Я так понимаю работает так
1. цепочка OUTPUT кидает на цепочку KUBE-SERVICES
2. KUBE-SERVICES видя IP-destination кидает на цепочку KUBE-SVC-...
3. KUBE-SVC-... распределяет нагрузку и кидает на одну из KUBE-SEP-...
4. KUBE-SEP-... делает DNAT на конкретную машину
 
## 1.4. Включение режима балансировки IPVS
### 1.4.0 Включим IPVS
```
kubectl --namespace kube-system edit configmap/kube-proxy
```

ищем KubeProxyConfig
меняем ```mode: ""``` => ```mode: "ipvs"```


#### 1.4.1 Перезагружаем kube-proxy
```
kubectl --namespace kube-system delete pod --selector='k8s-app=kube-proxy'
```

#### 1.4.2 Создадим файл /tmp/iptables.cleanup
minikube ssh
vi /tmp/iptables.cleanup
```
*nat
-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
COMMIT
*filter
COMMIT
*mangle
COMMIT
```
            
#### 1.4.3 Применим конфигурацию
```
$ iptables-restore /tmp/iptables.cleanup
```

#### 1.4.4 Через 30 секунд kube-proxy восстановит правила для подов
```
$ iptables --list -nv -t nat
```

#### 1.4.5 IPVS
```            
$ toolbox
$ dnf install -y ipvsadm && dnf clean all
$ dnf install -y ipset && dnf clean all
$ ipvsadm --list -n
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
TCP  10.96.0.1:443 rr
  -> 192.168.99.134:8443          Masq    1      0          0         
TCP  10.96.0.10:53 rr
  -> 172.17.0.2:53                Masq    1      0          0         
  -> 172.17.0.3:53                Masq    1      0          0         
TCP  10.96.0.10:9153 rr
  -> 172.17.0.2:9153              Masq    1      0          0         
  -> 172.17.0.3:9153              Masq    1      0          0         
TCP  10.106.8.233:80 rr
  -> 172.17.0.4:8000              Masq    1      0          0         
  -> 172.17.0.5:8000              Masq    1      0          0         
  -> 172.17.0.6:8000              Masq    1      0          0         
UDP  10.96.0.10:53 rr
  -> 172.17.0.2:53                Masq    1      0          0         
  -> 172.17.0.3:53                Masq    1      0          0  
```

#### 1.4.6 Ping ClusterIP
```
$ ping  10.106.8.233
PING 10.106.8.233 (10.106.8.233): 56 data bytes
64 bytes from 10.106.8.233: seq=0 ttl=64 time=0.146 ms
^C
--- 10.106.8.233 ping statistics ---
1 packets transmitted, 1 packets received, 0% packet loss
round-trip min/avg/max = 0.146/0.146/0.146 ms
```


#### 1.4.7 Интерфейс IPVS

```
$ ip addr show kube-ipvs0
66: kube-ipvs0: <BROADCAST,NOARP> mtu 1500 qdisc noop state DOWN group default 
    link/ether 8a:bc:f8:fc:f3:fb brd ff:ff:ff:ff:ff:ff
    inet 10.106.8.233/32 brd 10.106.8.233 scope global kube-ipvs0
       valid_lft forever preferred_lft forever
    inet 10.96.0.1/32 brd 10.96.0.1 scope global kube-ipvs0
       valid_lft forever preferred_lft forever
    inet 10.96.0.10/32 brd 10.96.0.10 scope global kube-ipvs0
       valid_lft forever preferred_lft forever
$ ip addr show | gre pipvs
-bash: gre: command not found
$ ip addr show | grep ipvs
66: kube-ipvs0: <BROADCAST,NOARP> mtu 1500 qdisc noop state DOWN group default 
    inet 10.106.8.233/32 brd 10.106.8.233 scope global kube-ipvs0
    inet 10.96.0.1/32 brd 10.96.0.1 scope global kube-ipvs0
    inet 10.96.0.10/32 brd 10.96.0.10 scope global kube-ipvs0
$ 
```

#### 1.4.8 ipset
```
ipset list
Name: KUBE-NODE-PORT-UDP
Type: bitmap:port
Revision: 3
Header: range 0-65535
Size in memory: 8268
References: 0
Number of entries: 0
Members:

Name: KUBE-NODE-PORT-LOCAL-UDP
Type: bitmap:port
Revision: 3
Header: range 0-65535
Size in memory: 8268
References: 0
Number of entries: 0
Members:

Name: KUBE-NODE-PORT-LOCAL-SCTP-HASH
Type: hash:ip,port
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 88
References: 0
Number of entries: 0
Members:

Name: KUBE-LOOP-BACK
Type: hash:ip,port,ip
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 816
References: 1
Number of entries: 9
Members:
172.17.0.2,udp:53,172.17.0.2
172.17.0.5,tcp:8000,172.17.0.5
172.17.0.3,tcp:9153,172.17.0.3
172.17.0.3,udp:53,172.17.0.3
172.17.0.2,tcp:53,172.17.0.2
172.17.0.6,tcp:8000,172.17.0.6
172.17.0.2,tcp:9153,172.17.0.2
172.17.0.3,tcp:53,172.17.0.3
172.17.0.4,tcp:8000,172.17.0.4

Name: KUBE-LOAD-BALANCER-SOURCE-IP
Type: hash:ip,port,ip
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 96
References: 0
Number of entries: 0
Members:

Name: KUBE-NODE-PORT-TCP
Type: bitmap:port
Revision: 3
Header: range 0-65535
Size in memory: 8268
References: 0
Number of entries: 0
Members:

Name: KUBE-NODE-PORT-LOCAL-TCP
Type: bitmap:port
Revision: 3
Header: range 0-65535
Size in memory: 8268
References: 0
Number of entries: 0
Members:

Name: KUBE-NODE-PORT-SCTP-HASH
Type: hash:ip,port
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 88
References: 0
Number of entries: 0
Members:

Name: KUBE-CLUSTER-IP
Type: hash:ip,port
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 408
References: 2
Number of entries: 5
Members:
10.96.0.10,tcp:9153
10.96.0.10,tcp:53
10.96.0.1,tcp:443
10.96.0.10,udp:53
10.106.8.233,tcp:80

Name: KUBE-LOAD-BALANCER
Type: hash:ip,port
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 88
References: 0
Number of entries: 0
Members:

Name: KUBE-LOAD-BALANCER-LOCAL
Type: hash:ip,port
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 88
References: 0
Number of entries: 0
Members:

Name: KUBE-LOAD-BALANCER-SOURCE-CIDR
Type: hash:ip,port,net
Revision: 7
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 352
References: 0
Number of entries: 0
Members:

Name: KUBE-EXTERNAL-IP
Type: hash:ip,port
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 88
References: 0
Number of entries: 0
Members:

Name: KUBE-LOAD-BALANCER-FW
Type: hash:ip,port
Revision: 5
Header: family inet hashsize 1024 maxelem 65536
Size in memory: 88
References: 0
Number of entries: 0
Members:
```

#### iptables
```
$ iptables --list -nv -t nat
Chain OUTPUT (policy ACCEPT 34 packets, 2040 bytes)
 pkts bytes target     prot opt in     out     source               destination         
 2246  136K KUBE-SERVICES  all  --  *      *       0.0.0.0/0            0.0.0.0/0            /* kubernetes service portals */

Chain KUBE-SERVICES (2 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 KUBE-MARK-MASQ  all  --  *      *       0.0.0.0/0            0.0.0.0/0            /* Kubernetes service cluster ip + port for masquerade purpose */ match-set KUBE-CLUSTER-IP src,dst
    8   480 KUBE-NODE-PORT  all  --  *      *       0.0.0.0/0            0.0.0.0/0            ADDRTYPE match dst-type LOCAL
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            match-set KUBE-CLUSTER-IP dst,dst

Chain KUBE-MARK-MASQ (2 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 MARK       all  --  *      *       0.0.0.0/0            0.0.0.0/0            MARK or 0x4000

Chain KUBE-NODE-PORT (1 references)
 pkts bytes target     prot opt in     out     source               destination  


```

## 2. Доступ к приложению извне кластера 

### 2.1. Установка MetaILB в Layer2 режиме
####  2.1.1 Установка
```
// $ kubectl apply -f https://raw.githubusercontent.com/google/metallb/v0.8.0/manifests/metallb.yaml
```
или
```
$ wget https://raw.githubusercontent.com/google/metallb/v0.8.0/manifests/metallb.yaml

$ kubectl apply -f metallb.yaml
namespace/metallb-system created
podsecuritypolicy.extensions/speaker created
serviceaccount/controller created
serviceaccount/speaker created
clusterrole.rbac.authorization.k8s.io/metallb-system:controller created
clusterrole.rbac.authorization.k8s.io/metallb-system:speaker created
role.rbac.authorization.k8s.io/config-watcher created
clusterrolebinding.rbac.authorization.k8s.io/metallb-system:controller created
clusterrolebinding.rbac.authorization.k8s.io/metallb-system:speaker created
rolebinding.rbac.authorization.k8s.io/config-watcher created
daemonset.apps/speaker created
deployment.apps/controller created

$ kubectl --namespace metallb-system get all
NAME                              READY   STATUS    RESTARTS   AGE
pod/controller-7757586ff4-qf6vh   1/1     Running   0          64s
pod/speaker-dn7s9                 1/1     Running   0          64s

NAME                     DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR                 AGE
daemonset.apps/speaker   1         1         1       1            1           beta.kubernetes.io/os=linux   64s

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/controller   1/1     1            1           64s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/controller-7757586ff4   1         1         1       64s
```


#### 2.1.2 Настройка балансировщика metallb-config.yaml
```
                apiVersion: v1
                kind: ConfigMap
                metadata:
                    namespace: metallb-system
                    name: config
                data:
                    config: |
                        address-pools:
                            - name: default
                              protocol: layer2
                              addresses:
                                - "172.17.255.1-172.17.255.255" 
```

```
$ kubectl apply -f metallb-config.yaml
configmap/config created
```

### 2.2. Добавление сервиса LoadBalancer
#### 2.2.1 Создаем файл web-svc-lb.yaml
```
                apiVersion: v1
                kind: Service
                metadata:
                    name: web-svc-lb
                spec:
                    selector:
                        app: web
                    type: LoadBalancer
                    ports:
                        - protocol: TCP
                        port: 80
                        targetPort: 8000
```

#### 2.2.2 Применяем и Проверяем
```
$ kubectl apply -f web-svc-lb.yaml
configmap/config created

$ kubectl --namespace metallb-system logs pod/controller-7757586ff4-qf6vh
{"caller":"main.go:75","event":"noChange","msg":"service converged, no change","service":"default/web-svc-cip","ts":"2020-05-11T22:18:39.444858983Z"}
{"caller":"main.go:76","event":"endUpdate","msg":"end of service update","service":"default/web-svc-cip","ts":"2020-05-11T22:18:39.444904995Z"}
{"caller":"main.go:49","event":"startUpdate","msg":"start of service update","service":"default/web-svc-lb","ts":"2020-05-11T22:33:58.742029661Z"}
{"caller":"service.go:98","event":"ipAllocated","ip":"172.17.255.1","msg":"IP address assigned by controller","service":"default/web-svc-lb","ts":"2020-05-11T22:33:58.742219702Z"}
{"caller":"main.go:96","event":"serviceUpdated","msg":"updated service object","service":"default/web-svc-lb","ts":"2020-05-11T22:33:58.832565394Z"}
{"caller":"main.go:98","event":"endUpdate","msg":"end of service update","service":"default/web-svc-lb","ts":"2020-05-11T22:33:58.832663293Z"}
{"caller":"main.go:49","event":"startUpdate","msg":"start of service update","service":"default/web-svc-lb","ts":"2020-05-11T22:33:58.832710008Z"}
{"caller":"main.go:75","event":"noChange","msg":"service converged, no change","service":"default/web-svc-lb","ts":"2020-05-11T22:33:58.833245964Z"}
{"caller":"main.go:76","event":"endUpdate","msg":"end of service update","service":"default/web-svc-lb","ts":"2020-05-11T22:33:58.833313127Z"}

$ kubectl describe svc web-svc-lb
Name:                     web-svc-lb
Namespace:                default
Labels:                   <none>
Annotations:              kubectl.kubernetes.io/last-applied-configuration:
                            {"apiVersion":"v1","kind":"Service","metadata":{"annotations":{},"name":"web-svc-lb","namespace":"default"},"spec":{"ports":[{"port":80,"p...
Selector:                 app=web
Type:                     LoadBalancer
IP:                       10.103.226.132
LoadBalancer Ingress:     172.17.255.1
Port:                     <unset>  80/TCP
TargetPort:               8000/TCP
NodePort:                 <unset>  32367/TCP
Endpoints:                172.17.0.4:8000,172.17.0.5:8000,172.17.0.6:8000
Session Affinity:         None
External Traffic Policy:  Cluster
Events:
  Type    Reason       Age   From                Message
  ----    ------       ----  ----                -------
  Normal  IPAllocated  84s   metallb-controller  Assigned IP "172.17.255.1"
```


#### 2.2.3 Создаем статический маршрут в основной ОС
```
$ minikube ip
192.168.99.134
$ ip route add 172.17.255.0/24 via 192.168.99.134
```
открываем страницу в браузере http://172.17.255.1/index.html

#### 2.2.4 DNS через MataILB
1. Создаем манифест coredns-svc-lb.yaml
```
---
apiVersion: v1
kind: Service
metadata:
  name: coredns-svc-lb-udp
  annotations:
    metallb.universe.tf/allow-shared-ip: coredns
  namespace: kube-system
spec:
  selector:
    k8s-app: kube-dns
  type: LoadBalancer
  loadBalancerIP: 172.17.255.2
  ports:
  - protocol: UDP
    port: 53
    targetPort: 53
---
apiVersion: v1
kind: Service
metadata:
  name: coredns-svc-lb-tcp
  annotations:
    metallb.universe.tf/allow-shared-ip: coredns
  namespace: kube-system
spec:
  selector:
    k8s-app: kube-dns
  type: LoadBalancer
  loadBalancerIP: 172.17.255.2
  ports:
  - protocol: TCP
    port: 53
    targetPort: 53
```

```
$ kubectl apply -f coredns-svc-lb.yaml
service/coredns-svc-lb-udp created
service/coredns-svc-lb-tcp created
```

2. Проверяем работу
```
nslookup web-svc-lb.default.svc.cluster.local 172.17.255.2
```

### 2.3. Установка ingress-контроллера и прокси ingress-nginx
#### 2.3.1 Установка
```
$ kubeclt apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.27.1/deploy/static/mandatory.yaml
mandatory.yaml
namespace/ingress-nginx created
configmap/nginx-configuration created
configmap/tcp-services created
configmap/udp-services created
serviceaccount/nginx-ingress-serviceaccount created
clusterrole.rbac.authorization.k8s.io/nginx-ingress-clusterrole created
role.rbac.authorization.k8s.io/nginx-ingress-role created
rolebinding.rbac.authorization.k8s.io/nginx-ingress-role-nisa-binding created
clusterrolebinding.rbac.authorization.k8s.io/nginx-ingress-clusterrole-nisa-binding created
deployment.apps/nginx-ingress-controller created
limitrange/ingress-nginx created
```

            
#### 2.3.2 Создаем файл nginx-lb.yaml
```
kind: Service
apiVersion: v1
metadata:
  name: ingress-nginx
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
spec:
  externalTrafficPolicy: Local
  type: LoadBalancer
  selector:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
  ports:
    - { name: http, port: 80, targetPort: http }
    - { name: https, port: 443, targetPort: https }
```
            
#### 2.3.3 Применим
```
$ kubectl apply -f nginx-lb.yaml
service/ingress-nginx created

$ kubectl get services -n ingress-nginx
ingress-nginx                        LoadBalancer   10.111.117.209   172.17.255.3   80:31797/TCP,443:30634/TCP   23s
ingress-nginx-controller             NodePort       10.104.246.153   <none>         80:31819/TCP,443:31472/TCP   2m59s
ingress-nginx-controller-admission   ClusterIP      10.106.126.216   <none>         443/TCP                      2m59s

$ curl 172.17.255.3
<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx/1.17.7</center>
</body>
</html>

$ ping 172.17.255.3
PING 172.17.255.3 (172.17.255.3) 56(84) bytes of data.
64 bytes from 172.17.255.3: icmp_seq=1 ttl=64 time=0.540 ms
64 bytes from 172.17.255.3: icmp_seq=2 ttl=64 time=0.272 ms
^C
--- 172.17.255.3 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 8ms
rtt min/avg/max/mdev = 0.272/0.406/0.540/0.134 ms
```

#### 2.3.4 Создание Headless сервиса web-svc-headless.yaml
```
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  selector:
    app: web
  type: ClusterIP
  clusterIP: None
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

```
$ kubectl apply -f web-svc-headless.yaml
service/web-svc created

$ kubectl get services
kubernetes    ClusterIP      10.96.0.1        <none>         443/TCP        8h
web-svc       ClusterIP      None             <none>         80/TCP         69s
web-svc-cip   ClusterIP      10.106.8.233     <none>         80/TCP         3h40m
web-svc-lb    LoadBalancer   10.103.226.132   172.17.255.1   80:32367/TCP   82m
```


### 2.4. Создание правил Ingress
#### 2.4.1 Создаем файл web-ingress.yaml
```
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: web
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - http:
        paths:
          - path: /web
            backend:
              serviceName: web-svc
              servicePort: 8000
```

#### 2.4.2 Проверяем
```
$ kubectl apply -f web-ingress.yaml
ingress.networking.k8s.io/web created

$ kubectl describe ingress/web
Name:             web
Namespace:        default
Address:          172.17.255.3
Default backend:  default-http-backend:80 (<none>)
Rules:
  Host  Path  Backends
  ----  ----  --------
  *     
        /web   web-svc:8000 (172.17.0.4:8000,172.17.0.5:8000,172.17.0.6:8000)
Annotations:
  kubectl.kubernetes.io/last-applied-configuration:  {"apiVersion":"networking.k8s.io/v1beta1","kind":"Ingress","metadata":{"annotations":{"nginx.ingress.kubernetes.io/rewrite-target":"/"},"name":"web","namespace":"default"},"spec":{"rules":[{"http":{"paths":[{"backend":{"serviceName":"web-svc","servicePort":8000},"path":"/web"}]}}]}}

  nginx.ingress.kubernetes.io/rewrite-target:  /
Events:
  Type    Reason  Age   From                      Message
  ----    ------  ----  ----                      -------
  Normal  CREATE  22s   nginx-ingress-controller  Ingress default/web
  Normal  UPDATE  20s   nginx-ingress-controller  Ingress default/web
```

открываем страницу http://172.17.255.3/web/index.html

#### 2.4.3 Dashboard проверка
```
$ kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-beta1/aio/deploy/recommended.yaml
namespace/kubernetes-dashboard created
serviceaccount/kubernetes-dashboard created
service/kubernetes-dashboard created
secret/kubernetes-dashboard-certs created
secret/kubernetes-dashboard-csrf created
secret/kubernetes-dashboard-key-holder created
configmap/kubernetes-dashboard-settings created
role.rbac.authorization.k8s.io/kubernetes-dashboard created
clusterrole.rbac.authorization.k8s.io/kubernetes-dashboard created
rolebinding.rbac.authorization.k8s.io/kubernetes-dashboard created
clusterrolebinding.rbac.authorization.k8s.io/kubernetes-dashboard created
deployment.apps/kubernetes-dashboard created
service/dashboard-metrics-scraper created
deployment.apps/kubernetes-metrics-scraper created

$ kubectl apply -f dashboard-ingress.yaml
ingress.networking.k8s.io/dashboard-ing created

$ kubectl describe ingress/dashboard-ing -n kube-system
Name:             dashboard-ing
Namespace:        kube-system
Address:          172.17.255.3
Default backend:  default-http-backend:80 (<none>)
Rules:
  Host  Path  Backends
  ----  ----  --------
  *     
        /dashboard(/|$)(.*)   kubernetes-dashboard:80 (<none>)
Annotations:
  kubectl.kubernetes.io/last-applied-configuration:  {"apiVersion":"networking.k8s.io/v1beta1","kind":"Ingress","metadata":{"annotations":{"nginx.ingress.kubernetes.io/rewrite-target":"/$2"},"name":"dashboard-ing","namespace":"kube-system"},"spec":{"rules":[{"http":{"paths":[{"backend":{"serviceName":"kubernetes-dashboard","servicePort":80},"path":"/dashboard(/|$)(.*)"}]}}]}}

  nginx.ingress.kubernetes.io/rewrite-target:  /$2
Events:
  Type    Reason  Age   From                      Message
  ----    ------  ----  ----                      -------
  Normal  CREATE  86s   nginx-ingress-controller  Ingress kube-system/dashboard-ing
  Normal  UPDATE  72s   nginx-ingress-controller  Ingress kube-system/dashboard-ing

$ sudo nano /etc/hosts
...
172.17.255.3    example.app.org
...

$ curl -kL http://example.app.org/dashboard/
```

#### 2.4.4 Canary проверка
```
$ kubectl apply -f canary/current-deploy.yaml
$ kubectl apply -f canary/current-ingress.yaml
$ kubectl apply -f canary/canary-deploy.yaml
$ kubectl apply -f canary/canary-ingress.yaml

$ curl -kL http://example.app.org/test-webapp
v1

$ curl -kL --header 'mtest: true'  http://example.app.org/test-webapp
v2
```


