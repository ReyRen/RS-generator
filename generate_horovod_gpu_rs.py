#!/usr/bin/env python2
#-*- coding: UTF-8 -*-

import yaml
import logging
import os
import sys
import time
import subprocess


def print_msg(svcName, port, svcSelector, podName, containerName, mount_path, volume_name, claim_name):

    print("\033[0;32m====> svc.metadata.name: %s\033[0m"%(svcName))
    print("\033[0;32m====> svc.metadata.namespace: %s\033[0m"%(namespace))
    print("\033[0;32m====> svc.spec.ports.port: %s\033[0m"%(port))
    print("\033[0;32m====> svc.spec.selector.run: %s\033[0m"%(svcSelector))
    print("\033[0;32m====> pod.metadata.name: %s\033[0m"%(podName))
    print("\033[0;32m====> pod.spec.containers.image: %s\033[0m"%(image_name))
    print("\033[0;32m====> pod.spec.containers.name: %s\033[0m"%(containerName))
    print("\033[0;32m====> pod.spec.containers.volumeMounts.name: %s\033[0m"%(volume_name))
    print("\033[0;32m====> pod.spec.containers.volumeMounts.mountPath: %s\033[0m"%(mount_path))
    print("\033[0;32m====> pod.spec.volumes.name: %s\033[0m"%(volume_name))
    print("\033[0;32m====> pod.spec.volumes.persistentVolumeClaim.persistentVolumeClaim: %s\033[0m"%(claim_name))

def generate_service_template(serviceName, selectorName):

    py_object = {
                'apiVersion':'v1',
                'kind':'Service',
                'metadata':{'name':serviceName,'namespace':namespace,'labels':{'run':selectorName}},
                'spec':{'selector':{'run':selectorName},'ports':[{'name':'ssh','protocol':'TCP','port':22,'targetPort':22}]}
                }

    return py_object

def get_running_status():
    strings = r"kubectl get pods -n ai -l run=" + svcSelector + r" | awk -v RS='Running' 'END {print --NR}'"
    f = os.popen(strings)
    contents = f.read()
    if contents.rstrip() == gpu_num:
        return True
    return False

def get_net1_ip(podName):
# kubectl exec -it pod-slave18 -n ai -- hostname -I |  awk '{print $2}'
    popenCmd = r"kubectl exec -it " + podName + " -n " + namespace + r" -- hostname -I |  awk '{print $2}'"
    f = os.popen(popenCmd)
    netIp = f.read()
    f.close()

    return netIp

def print_wait_msg(num):

    for i in range(1,int(num) + 1):
        sys.stdout.write("*")
        sys.stdout.flush()
        time.sleep( 1 )

    print("")

def generate_gpu_pod():

    master_pod_list = []
    arg_extra_ssh = ""

    # ready to yaml file
    current_path = os.path.abspath(".")


    # common selector label
    #svcSelector = "radar"

    # PVC
    mount_path = "/usr/share/horovod"
    volume_name = "nfs-volume"
    claim_name = "pod-pvc-volume-1"

    # exec cmd
    arg_pod = arg_base
    arg_pod += "ssh-keygen -t rsa -P \"\" -f ~/.ssh/id_rsa;tail -f /dev/null;"
    list_arg_pod.append(arg_pod)

    for i in range(1, int(gpu_num) + 1):
        if i == 1:
            # only master
            svcNameMaster = "radar-master-svc"
            podNameMaster = "radar-master"
            containerMaster = "radar-master-container"
            file_name = "radar-master.yaml" 

            masterSvcObj = generate_service_template(svcNameMaster, svcSelector)
            masterPodObj = {
                            'apiVersion':'v1',
                            'kind':'Pod',
                            'metadata':{'name':podNameMaster,'namespace':namespace,'labels':{'run':svcSelector},'annotations':{'k8s.v1.cni.cncf.io/networks':'macvlan-conf'}},
                            'spec':{'containers':[{'name':containerMaster,'image':image_name,'command':['/bin/sh','-c'],'args':list_arg_pod,'resources':{'limits':{'nvidia.com/gpu':1}},'volumeMounts':[{'name':volume_name,'mountPath':mount_path}]}],'volumes':[{'name':volume_name,'persistentVolumeClaim':{'claimName':claim_name}}]}}
            # join
            file = open(os.path.join(current_path, file_name), 'w')
            yaml.dump_all([masterSvcObj,masterPodObj], file)
            file.close()

            if exec_true == "true":
                k8s_apply = "kubectl apply -f " + os.path.join(current_path, file_name)
                os.system(k8s_apply)
                master_pod_list.append(podNameMaster)
            print_msg(svcNameMaster, 22, svcSelector, podNameMaster, containerMaster, mount_path, volume_name, claim_name)
            continue
        num = i - 1
        svcNameSlave = ''.join(['radar-slave-svc', str(num)])
        podNameSlave = ''.join(['radar-slave', str(num)])
        containerSlave = ''.join(['radar-slave-container', str(num)])
        file_name = ''.join(['radar-slave', str(num), '.yaml'])

        slaveSvcObj = generate_service_template(svcNameSlave, svcSelector)
        slavePodObj = {
                      'apiVersion':'v1',
                      'kind':'Pod',
                      'metadata':{'name':podNameSlave,'namespace':namespace,'labels':{'run':svcSelector},'annotations':{'k8s.v1.cni.cncf.io/networks':'macvlan-conf'}},
                      'spec':{'containers':[{'name':containerSlave,'image':image_name,'command':['/bin/sh','-c'],'args':list_arg_pod,'resources':{'limits':{'nvidia.com/gpu':1}},'volumeMounts':[{'name':volume_name,'mountPath':mount_path}]}],'volumes':[{'name':volume_name,'persistentVolumeClaim':{'claimName':claim_name}}]}}
        # join
        file = open(os.path.join(current_path, file_name), 'w')
        yaml.dump_all([slaveSvcObj,slavePodObj], file)
        file.close()
        print_msg(svcNameSlave, 22, svcSelector, podNameSlave, containerSlave, mount_path, volume_name, claim_name)

        if exec_true == "true":
            k8s_apply = "kubectl apply -f " + os.path.join(current_path, file_name)
            os.system(k8s_apply)
            master_pod_list.append(podNameSlave)
    print("\033[1;33mPlease wait for a minute to let pod startup and ready the env...\033[3,31m")
    print_wait_msg(30)
    while not get_running_status():
        print("\033[1;33mPlease wait for a minute to let pod startup and ready the env...\033[3,31m")
        print_wait_msg(10)
    print("\033[1;33mInstall some small components and transfer ssh keys\033[3,31m")
    print_wait_msg(20)
    i = 1
    arg_training = "kubectl exec "+ podNameMaster  + " -n " + namespace + " -it --  horovodrun -np " + gpu_num + " -H "
    for l in master_pod_list:
        ipStr = get_net1_ip(l).rstrip()
        fd.write(ipStr)
        arg_extra_ssh = "kubectl exec " + podNameMaster + " -n " + namespace + " -it -- " + "sshpass -p admin123 ssh-copy-id root@" + ipStr
        arg_training += ipStr + ":1"
        if i < int(gpu_num):
            arg_training += ","
            i = i + 1
        #os.system(arg_extra_ssh)
        ret = subprocess.call(arg_extra_ssh, bufsize=0, stdout=fd, shell = True)
        if ret == 0:
            os.system("kubectl delete pods -n ai -l run=radar")
    arg_training += " python /usr/share/horovod/tmp-yolov3/distributed_train.py "
    #ret = subprocess.call(arg_training, bufsize=0, stdout=fd, shell = True)
        


if __name__ == '__main__':
    try:
        namespace = sys.argv[1]
        gpu_num = sys.argv[2] # this num stand by the number of GPU pods
        exec_true = sys.argv[3]

        list_arg_pod = []

        fd = open("/tmp/training.log", 'a')
        fd.truncate()


        # TODO:some paramaters can be modified
        image_name = "horovod/horovod:0.18.1-tf1.14.0-torch1.2.0-mxnet1.5.0-py3.6-special"
        #image_name = "horovod/horovod:0.18.1-tf1.14.0-torch1.2.0-mxnet1.5.0-py3.6"
        # base command
        arg_base = 'apt update -y;apt install ssh sshpass -y;echo root:admin123|chpasswd;tmp=\"PermitRootLogin yes\";sed -i \"/^#PermitRootLogin/c$tmp\" /etc/ssh/sshd_config;/etc/init.d/ssh restart; '
        svcSelector = "radar"

        generate_gpu_pod()

#if not os.path.exists(yaml_path):
        logging.info("Created RS in %s namespaces." %(namespace))
        fd.close()
    except IOError as e:
        logging.error("Failed to create RS in %s namespaces: {}" %(namespace))
