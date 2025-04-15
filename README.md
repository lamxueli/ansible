# Ansible 自动化部署指南

## 1. 环境配置

### 安装必要软件及配置
```bash
# 安装Ansible
sudo pip install ansible
# 安装sshpass（用于密码登录）
sudo apt-get install -y sshpass

# 登录目标主机（替换实际IP）
ssh eai@10.10.xx.xx
# 在目标主机上安装SSH服务
sudo apt-get install -y ssh
sudo service sshd start
exit

# 复制公钥到目标主机
ssh-copy-id -i ./.ssh/id_ed25519.pub eai@22.22.99.999
# 验证登录
ssh eai@10.10.xx.xx # 成功应无需输入密码
```

## 2.使用ansible
```bash
cd ./ansible
# 测试主机连通性
ansible-playbook -i ./inventory/hosts ./playbook/ping.yaml

# git clone 操作
ansible-playbook -i ./inventory/hosts ./playbook/gitclone.yaml
# 若目标文件夹不为空 input "yes" 删除内容
```
