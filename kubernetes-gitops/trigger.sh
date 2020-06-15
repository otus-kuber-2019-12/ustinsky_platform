#!/bin/bash

if [[ $1 -eq 0 ]]
then
  openssl rand -hex 12 | cat > ./src/$1/trigger
  git add -A
  git commit -am "Trigger $1"
else
  for d in ./src/* ; do
    openssl rand -hex 12 | cat > $d/trigger 
  done 
  git add -A
  git commit -am 'Trigger all microservices'
  git push origin master 
fi


