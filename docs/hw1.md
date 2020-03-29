Домашняя работа 1 (kuber-intro)

## 1.    Установка kubectl <br>
https://kubernetes.io/docs/tasks/tools/install-kubectl/

### 1.1   Скачиваем
```
curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl
``` 

curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl

### 1.2   Даем права 
```
chmod +x ./kubectl
```
    
### 1.3 Переносим в /usr/local/bin
~~~~
sudo mv ./kubectl /usr/local/bin/kubectl
~~~~  

### 1.4 Переносим в /usr/local/bin
~~~~
kubectl version --client
~~~~

### 1.5 Настраиваем автодополнение
~~~~
source <(kubectl completion bash)
echo "source <(kubectl completion bash)" >> ~/.bash_profile
~~~~
    
## 2.  Установка minikube <br>
https://kubernetes.io/docs/tasks/tools/install-minikube/

### 2.1 Проверяем наличие поддержки аппаратной виртуализации
~~~~
grep -E --color 'vmx|svm' /proc/cpuinfo
~~~~
Должны вывести строки, если все пусто - то аппаратная виртуализация не поддерживается


### 2.2 Устанавливаем VirtualBox
https://www.virtualbox.org/wiki/Downloads


### 2.3 Скачиваем minikube
~~~~
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && chmod +x minikube
~~~~


### 2.4 Устанавливаем minikube
~~~~
sudo install minikube /usr/local/bin
~~~~

### 2.5 Запуск minikube <br>
~~~~
minikube start
~~~~

## 3. Установка kind (https://kind.sigs.k8s.io/) <br>
### 3.1. Ставим
~~~~
GO111MODULE="on" go get sigs.k8s.io/kind@v0.7.0 && kind create cluster
~~~~

### 3.2. Опредеяем настройки kubectl
~~~~
export KUBECONFIG="$(kind get kubeconfig-path --name="kind")"
~~~~

### 3.3. Проверяем кластер
~~~~
kubectl cluster-info
~~~~

## 4. Просмотр текущей конфигурации <br>
### 4.1 kubectl 
~~~~
        kubectl config view
~~~~
    
### 4.2 Подключение к кластеру
~~~~
        kubectl cluster-info
~~~~

## 5.  Kubernetes Dashboard <br>
https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/
### 5.1 Применяем
~~~~
        wget https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-beta8/aio/deploy/recommended.yaml
        mv recommended.yaml kube-web-ui-dashboard-recommended.yaml
        kubectl apply -f kube-web-ui-dashboard-recommended.yaml
~~~~
### 5.2 Доступ (https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/)

#### 5.2.1 dashboard-service-account.yaml
~~~~
            apiVersion: v1
            kind: ServiceAccount
            metadata:
                name: admin-user
                namespace: kube-system
~~~~        
        
#### 5.2.2 dashboard-role-binding.yaml
~~~~
            apiVersion: rbac.authorization.k8s.io/v1
            kind: ClusterRoleBinding
            metadata:
                name: admin-user
            roleRef:
                apiGroup: rbac.authorization.k8s.io
                kind: ClusterRole
                name: cluster-admin
            subjects:
            -   kind: ServiceAccount
                name: admin-user
                namespace: kube-system
~~~~

#### 5.2.3 Применяем
~~~~
kubectl apply -f dashboard-service-account.yaml
kubectl apply -f dashboard-role-binding.yaml
~~~~

#### 5.2.4 Смотрим токен
~~~~
            kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep admin-user | awk '{print $1}') 
~~~~

### 5.3 Проксируем
~~~~
            kubectl proxy
~~~~


### 5.4 Заходим на http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/ используя токен

## 6.  k9s <br>
Ссылка в методичке на https://k9ss.io/ не работает.
рабочая ссылка: https://github.com/derailed/k9s.

### 6.1 Скачиваем
~~~~ 
LC_ALL="en_US.UTF-8" brew install derailed/k9s/k9s
~~~~

для обновления
~~~~
brew upgrade k9s
~~~~

## 7.  Проверяем устойчивость <br>
### 7.1 Заходим на VM по SSH
~~~~
minikube ssh
~~~~
    
### 7.2 Проверяем устойчивость к отказам 
~~~~
docker rm -f $(docker ps -a -q)
~~~~

### 7.3 Проверяем устойчивость через kubectl. Получаем список pod-ов для namespace kube-system
~~~~
kubectl get pods -n kube-system
~~~~

### 7.4 Удаляем все поды для этого namespace
~~~~
kubectl delete pod --all -n kube-system
~~~~

### 7.5 Проверка что кластер находится в рабочем состоянии <br>
~~~~
    kubectl get componentstatuses
    kubectl get cs 
~~~~

## 7.6 Почему происходит восcтановление системных подов после удаления <br>
    kubelet запущен как сервис systemd. Он занимается процессом запуска pod-ов.
    Если выполнить 
    sudo systemctl stop kubelet; docker rm -f $(docker ps -a -q)
    то кластер не восстанавливается автоматически

    для запуска кластера
    sudo systemctl start kubelet;
    после чего кластер запускает необходимые контейнеры

    core-dns реализован как Deployment с параметром replicas: 2

    так же можно сломать кластер командой 
    (kill -9 `pgrep -f docker`) &


## 8. Создать Dockerfile в котором будет описан образ: <br>
    1. Запускающий web-сервер на порту 8000
    2. Отдающий содержимое директории /app
    3. Файл /app/homework.html
    4. Работающий с UID 1001
    5. разместить в kubernetes-intro/web 
    6. Собрать образ и разместить его в DockerHub

## 9. Написать манифест web-pod.yaml <br>
Образец макета манифеста:
~~~~
    apiVersion: v1      # Версия API 
    kind: Pod           # Объект, который создаем
    metadata:
        name:           # Название Pod
        labels:         # Метки в формате key: value
            key: value
    spec:               # Описание Pod
        containers:     # Описание контейнеров внутри Pod
            - name:     # Название контейнера
              image:    # Образ из которого создается контейнер
~~~~

### 9.1 Применить манифест и разметить в kubernetes-intro <br>
~~~~
kubectl apply -f web-pod.yaml
~~~~
### 9.2 Проверяем работу 
~~~~
kubectl get pods
~~~~

### 9.3 Получаем от kubernetes манифест уже запущенного pod-а  <br>
~~~~
kubectl get pod web -o yaml
~~~~

### 9.4 Получаем текущее состояние и события pod-а <br>
~~~~
kubectl describe pod web
~~~~

### 9.5 Успешная старт pod-а дает следующие сообщения: <br>
    1. scheduler определил где запускать pod
    2. kubelet скачал необходимый образ и запустил контейнер

### 9.6 Имитация неудачного старта <br>
Добавить в web-pod.yaml несуществующий тэг и применить
~~~~
kubectl apply -f web-pod.yaml
~~~~

Проверить вывод команды 
~~~~
kubectl get pods
kubectl describe pod web
~~~~

## 10. Init контейнеры: <br>
Добавим в манифест
~~~~
    image: busybox:1.31.0
    command: ['sh', '-c', 'wget -O- https://raw.githubusercontent.com/express42/otus-platform-snippets/master/Module-02/Introduction-to-Kubernetes/wget.sh | sh']
~~~~

### 10.1 Volume: <br>
Добавим
для контейнера:
~~~~
        volumeMounts:
            -name: app
             mountPath: /app
~~~~

для pod:
~~~~
        volumes:
            -name: app
             emptyDir: {}
~~~~

### 10.2 Удалить запущенный под из кластера и применить обновленный манифест <br>
~~~~
    kubectl delete pod web
    kubectl get pods -w
    kubectl apply -f web-pod.yaml && kubectl get pods -w 
~~~~

### 10.3 Проверка работы приложения <br>
~~~~
    kubectl port-forward --address 0.0.0.0 pod/web 8000:8000
~~~~

открыть в браузере http://localhost:8000/index.html


## 11. Hipster Shop

### 11.1 Проверка работы приложения <br>

Склонируйте репозиторий и соберите собственный образ для frontend (используйте готовый Dockerfile)
~~~~    
git clone https://github.com/GoogleCloudPlatform/microservices-demo.git
cd microservices-demo/src/frontend
docker build .
docker tag  <id-image> austinsky/hipster-frontend:v0.0.1
~~~~

Поместите собранный образ на Docker Hub
~~~~
docker logout
docker login
docker push austinsky/hipster-frontend:v0.0.1
~~~~

### 11.2 Запустить через команду
~~~~
kubectl run frontend --image avtandilko/hipster-frontend:v0.0.1 --restart=Never
~~~~

или

~~~~
kubectl run frontend --image austinsky/hipster-frontend:v0.0.1 --restart=Never
~~~~

### 11.3 Сгенерируем манифест
~~~~
kubectl run frontend --image austinsky/hipster-frontend:v0.0.1 --restart=Never --dry-run -o yaml > frontend-pod.yaml
~~~~

### 11.4 Выясните причину, по которой pod frontend находится в статусе Error
Причина - не инициализированы переменные окружения при запуске программы 

Исправления - добавлены эти переменные в запуск пода

### 11.5 Создан новый манифест frontend-pod-healthy.yaml. При его применении ошибка должна исчезает.
![Running](frontend-running.png)
