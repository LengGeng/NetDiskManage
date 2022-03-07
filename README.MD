<h2 align="center">NetDisk Manage</h2>

<p align="center"><a href="https://github.com/LengGeng/NetDiskManage/network"><img alt="GitHub forks" src="https://img.shields.io/github/forks/LengGeng/NetDiskManage"></a> <a href="https://github.com/LengGeng/NetDiskManage/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/LengGeng/NetDiskManage"></a> <a href="https://github.com/LengGeng/NetDiskManage/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/LengGeng/NetDiskManage"></a> <a href="https://github.com/LengGeng/NetDiskManage/blob/master/LICENSE"><img alt="GitHub license" src="https://img.shields.io/github/license/LengGeng/NetDiskManage"></a></p>

## 📙 简介

NetDiskManage 是一个网盘管理程序，旨在方便用户整合管理多个网盘中的资源进行管理。

相比于下载功能 NetDiskManage 更着重于对于分享文件的管理。(当然，下载功能也是必不可少的。)
正因如此，你可以通过 NetDiskManage 构建一个用于管理你对外分享的文件的网站。而不仅仅只是传统的下载服务。

NetDiskManage 本身并不存储文件数据，而是对接百度网盘，依赖百度网盘提供的API接口提供服务。
从另一方面来说，只要百度网盘不删除相应的API，本项目就一直是可用的。

## 🍽 安装与使用

NetDiskManage 使用 Python3.7 进行开发。主要依赖于 `requests`、`fastapi`、`uvicorn` 这三个库，可以通过以下命令进行安装：

~~~shell
pip install requests
pip install fastapi
pip install uvicorn
~~~

## 🍬 功能与特点

- 支持绑定多个百度网盘账户，无需再担忧存储空间不够的问题。
- 支持目录映射，只开放分享网盘的某一个目录，保留用户其他不需要分享的文件。

## ❤ 帮助与支持

目前项目正处于发展阶段，代码可能存在些许问题，同时很多新更能还处于开发之中。你的建议与反馈对 NetDiskManage 的发展至关重要，感谢提交 bug 或建议

## 🍩 鸣谢

本项目受 [bp3](https://github.com/zhufenghua1998/bp3) 的启发从而进行，在此特别感谢。