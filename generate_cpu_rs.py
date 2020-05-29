#!/usr/bin/env python2
#-*- coding: UTF-8 -*-

import yaml
import logging
import os
import sys

def generate_service_doc(yaml_file):
    serviceName = raw_input("输入想要创建的service name(svc-testing): ")
    svcSelector = raw_input("输入想要被service管理的label name(testing-label): ")
    portName = raw_input("输入想要映射端口的别名: ")
    portProtocol = raw_input("输入映射端口的protocol: ")
    nodePort = raw_input("输入外部访问svc的端口: ")
    port = raw_input("请输入集群访问svc的端口: ")
    targetPort = raw_input("请输入pod内部的端口: ")

    if serviceName == "":
        serviceName = "svc-testing"
    if svcSelector == "":
        svcSelector = "testing-label"
    if nodePort != "":
        nodePort = int(nodePort)
    if port != "":
        port = int(port)
    if targetPort != "":
        targetPort = int(targetPort)
    
    py_object = {
                'apiVersion':'v1',
                'kind':'Service',
                'metadata':{'name':serviceName,'namespace':namespace},
                'spec':{'type':'NodePort','selector':{'run':svcSelector},'ports':[{'name':portName,'protocol':portProtocol,'nodePort':nodePort,'port':port,'targetPort':targetPort}]}
                }
    file = open(yaml_file, 'w')
    yaml.dump(py_object, file)
    file.close()

def generate_deployment_doc(yaml_file):

    deploymentName = raw_input("输入想要创建的Deployment名称(pod-testing): ")
    replicasNum = raw_input("输入想要创建的replicas数量(1): ")
    matchLabels = raw_input("输入想要创建的matchLabels名称(testing-label): ")
    containerName = raw_input("输入想要创建的容器的名称(testing-container): ")
    imageName = raw_input("输入想要创建的image的名称: ")
    commandStr = raw_input("输入想要提前执行的命令: ")
    gpuNum = raw_input("输入想要使用的GPU个数(0): ")
    volumeMountsName = raw_input("输入想要挂在的逻辑卷名称(mount-name-testing): ")
    mountPath = raw_input("输入想要挂在的pod中的目录(/usr/share/horovod): ")
    pvcName = raw_input("输入要使用的pvc(pod-pvc-volume-1): ")
    disktype = raw_input("输入想要绑定的node(none, optional: cpu-master gpu-node1/2/3): ")

    if deploymentName == "":
        deploymentName = "pod-testing"
    if replicasNum == "":
        replicasNum = "1"
    if matchLabels == "":
        matchLabels = "testing-label"
    if containerName == "":
        containerName = "testing-container"
    if imageName == "":
        print('ERROR: 请指定imageName')
        os._exit(1)
    if commandStr == "":
        commandStr = "[ \"/bin/bash\", \"-ce\", \"tail -f /dev/null\" ]"
    if gpuNum == "":
        gpuNum = "0"
    if volumeMountsName == "":
        volumeMountsName = "mount-name-testing"
    if mountPath == "":
        mountPath = "/usr/share/horovod"
    if pvcName == "":
        pvcName = "pod-pvc-volume-1"


    py_object = {
                'apiVersion':'apps/v1',
                'kind':'Deployment',
                'metadata':{'name':deploymentName,'namespace':namespace},
                'spec':{'replicas':int(replicasNum),
                        'selector':{'matchLabels':{'run':matchLabels}},
                        'template':{'metadata':{'labels':{'run':matchLabels}},
                                    'spec':{'containers':[{'name':containerName,'image':imageName,'command':commandStr, 'resources':{'limits':{'nvidia.com/gpu':int(gpuNum)}},'volumeMounts':[{'name':volumeMountsName, 'mountPath':mountPath}]}],
                                             'nodeSelector':{'disktype':disktype},
                                             'volumes':[{'name':volumeMountsName,'persistentVolumeClaim':{'claimName':pvcName}}]}}
                                    
                                    }
                }
    file = open(yaml_file, 'w')
    yaml.dump(py_object, file)
#   yaml.dump_all([py_object,py_object2], file)

    file.close()

def generate_pod_doc(yaml_file):
    serviceName = raw_input("输入想要创建的service name(svc-testing): ")
    svcSelector = raw_input("输入想要被service管理的label name(testing-label): ")
    portName = raw_input("输入想要映射端口的别名: ")
    portProtocol = raw_input("输入映射端口的protocol: ")
    nodePort = raw_input("输入外部访问svc的端口: ")
    port = raw_input("请输入集群访问svc的端口: ")
    targetPort = raw_input("请输入pod内部的端口: ")

    if serviceName == "":
        serviceName = "svc-testing"
    if svcSelector == "":
        svcSelector = "testing-label"
    if nodePort != "":
        nodePort = int(nodePort)
    if port != "":
        port = int(port)
    if targetPort != "":
        targetPort = int(targetPort)
    
    py_object = {
                'apiVersion':'v1',
                'kind':'Service',
                'metadata':{'name':serviceName,'namespace':namespace},
                'spec':{'type':'NodePort','selector':{'run':svcSelector},'ports':[{'name':portName,'protocol':portProtocol,'nodePort':nodePort,'port':port,'targetPort':targetPort}]}
                }
    file = open(yaml_file, 'w')
    yaml.dump(py_object, file)
    file.close()

def generate_job_doc(yaml_file):
    serviceName = raw_input("输入想要创建的service name(svc-testing): ")
    svcSelector = raw_input("输入想要被service管理的label name(testing-label): ")
    portName = raw_input("输入想要映射端口的别名: ")
    portProtocol = raw_input("输入映射端口的protocol: ")
    nodePort = raw_input("输入外部访问svc的端口: ")
    port = raw_input("请输入集群访问svc的端口: ")
    targetPort = raw_input("请输入pod内部的端口: ")

    if serviceName == "":
        serviceName = "svc-testing"
    if svcSelector == "":
        svcSelector = "testing-label"
    if nodePort != "":
        nodePort = int(nodePort)
    if port != "":
        port = int(port)
    if targetPort != "":
        targetPort = int(targetPort)
    
    py_object = {
                'apiVersion':'v1',
                'kind':'Service',
                'metadata':{'name':serviceName,'namespace':namespace},
                'spec':{'type':'NodePort','selector':{'run':svcSelector},'ports':[{'name':portName,'protocol':portProtocol,'nodePort':nodePort,'port':port,'targetPort':targetPort}]}
                }
    file = open(yaml_file, 'w')
    yaml.dump(py_object, file)
    file.close()


if __name__ == '__main__':
    try:
        namespace = sys.argv[1]
        rstype = sys.argv[2]

        current_path = os.path.abspath(".")
        if rstype == "Deployment":
            yaml_path = os.path.join(current_path, "Deployment.yaml")
            generate_deployment_doc(yaml_path)
        elif rstype == "Service":
            yaml_path = os.path.join(current_path, "Service.yaml")
            generate_service_doc(yaml_path)
        elif rstype == "Pod":
            yaml_path = os.path.join(current_path, "Pod.yaml")
            generate_pod_doc(yaml_path)
        elif rstype == "Job":
            yaml_path = os.path.join(current_path, "Job.yaml")
            generate_job_doc(yaml_path)

        logging.info("Created RS in %s namespaces." %(namespace))
    except IOError as e:
        logging.error("Failed to create RS in %s namespaces: {}" %(namespace))

# apt update -y; apt install ssh vim -y; tmp="PermitRootLogin yes"; sed -i "/^#PermitRootLogin/c$tmp" /etc/ssh/sshd_conf; /etc/init.d/ssh restart
# echo root:admin123|chpasswd
