#!/usr/bin/env python2
#-*- coding: UTF-8 -*-

import yaml
import logging
import os
import sys

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
                'metadata':{'name':serviceName,'namespace':namespace},
                'spec':{'selector':{'run':selectorName},'ports':[{'name':'ssh','protocol':'TCP','port':22,'targetPort':22}]}
                }

    return py_object

def generate_cpu_pod_slave(yaml_file, num):

    # generate service
    svcName = ''.join(['pod-svc-slave', str(num)])
    svcSelector = ''.join(['pod-selector-slave', str(num)])
    mount_path = "/usr/share/horovod"
    volume_name = "volume-name"
    claim_name = "pod-pvc-volume-1"
    py_object_svc = generate_service_template(svcName, svcSelector)

    # generate pod
    arg_pod = arg_base
    arg_pod+="tail -f /dev/null;"
    list_arg_pod.append(arg_pod)
    podName = ''.join(['pod-slave', str(num)])
    containerName = ''.join(['pod-container-slave', str(num)])
    py_object = {
                'apiVersion':'v1',
                'kind':'Pod',
                'metadata':{'name':podName,'namespace':namespace,'labels':{'run':svcSelector}},
                'spec':{'containers':[{'name':containerName,'image':image_name,'command':['/bin/sh','-c'],'args':list_arg_pod,'volumeMounts':[{'name':volume_name,'mountPath':mount_path}]}],'volumes':[{'name':volume_name,'persistentVolumeClaim':{'claimName':claim_name}}]}}
    
    # join
    file = open(yaml_file, 'w')
    yaml.dump_all([py_object_svc, py_object], file)
    file.close()

    print_msg(svcName, 22, svcSelector, podName, containerName, mount_path, volume_name, claim_name)


def generate_cpu_job_slave(yaml_file):
    # generate service
    svcName = "job-svc-master"
    svcSelector = "job-selector-master"
    mount_path = "/usr/share/horovod"
    volume_name = "volume-name"
    claim_name = "pod-pvc-volume-1"
    py_object_svc = generate_service_template(svcName, svcSelector)

    # generate job
    jobName = "job-master"
    containerName = "job-container-master"
    arg_extra=arg_base
    arg_extra+="ssh-keygen -t rsa -P \"\" -f ~/.ssh/id_rsa;"
    arg_extra_ssh = ""
    arg_extra_exec = ""
    for i in range(1, int(cpu_num)+1):
        if i == 1:
            arg_extra_ssh = "sshpass -p admin123 ssh-copy-id root@" + svcName + "." + namespace + ".svc.cluster.local;"
            arg_extra_exec = "horovodrun -np " + cpu_num + " -H " + svcName + "." + namespace + ".svc.cluster.local:4"
            continue
        num = i - 1
        svcName = ''.join(['pod-svc-slave', str(num)])
        arg_extra_ssh += "sshpass -p admin123 ssh-copy-id root@" + svcName + "." + namespace + ".svc.cluster.local;"
        arg_extra_exec += "," + svcName + "." + namespace + ".svc.cluster.local:4"


    arg_extra = arg_extra + arg_extra_ssh + arg_extra_exec + " python myTrain_horovod_without_summary.py > result 2>&1"
    list_arg_job.append(arg_extra)

    py_object = {
                'apiVersion':'batch/v1',
                'kind':'Job',
                'metadata':{'name':jobName,'namespace':namespace,'labels':{'run':svcSelector}},
                'spec':{'template':{'metadata':{'name':'job-master','labels':{'run':svcSelector}},'spec':{'containers':[{'name':containerName,'image':image_name,'command':['/bin/sh','-c'],'args':list_arg_job,'volumeMounts':[{'name':volume_name,'mountPath':mount_path}]}],'volumes':[{'name':volume_name,'persistentVolumeClaim':{'claimName':claim_name}}],'restartPolicy':'Never'}}}}

    # join
    file = open(yaml_file, 'w')
    yaml.dump_all([py_object_svc, py_object], file)
    file.close()

    print_msg(svcName, 22, svcSelector, jobName, containerName, mount_path, volume_name, claim_name)

if __name__ == '__main__':
    try:
        namespace = sys.argv[1]
        cpu_num = sys.argv[2] # this num stand by the number of GPU pods
        exec_true = sys.argv[3]

        list_arg_pod = []
        list_arg_job = []

        # TODO:some paramaters can be modified
        image_name = "horovod/horovod:0.18.1-tf1.14.0-torch1.2.0-mxnet1.5.0-py3.6"
        # base command
        arg_base = 'cd /usr/share/horovod/SSD-Tensorflow/;apt update -y;apt install ssh vim sshpass -y;echo root:admin123|chpasswd;tmp=\"PermitRootLogin yes\";sed -i \"/^#PermitRootLogin/c$tmp\" /etc/ssh/sshd_config;/etc/init.d/ssh restart; '

        current_path = os.path.abspath(".")

        if cpu_num > 1:
            for i in range(1,int(cpu_num)):
                file_name = ''.join(['cpu-pod-slave', str(i), '.yaml'])
                yaml_path = os.path.join(current_path, file_name)
                if not os.path.exists(yaml_path):
                    generate_cpu_pod_slave(yaml_path, i)
                    print("%s created"%(yaml_path))
                else:
                    print("%s already exists"%(yaml_path))
                if exec_true == "true":
                    k8s_apply = "kubectl apply -f " + yaml_path
                    os.system(k8s_apply)

        yaml_path = os.path.join(current_path, "cpu-job-master.yaml")
        if not os.path.exists(yaml_path):
            generate_cpu_job_slave(yaml_path)
            print("%s created"%("cpu-job-master.yaml"))
        else:
            print("%s already exists"%(yaml_path))
        if exec_true == "true":
            os.system("kubectl apply -f cpu-job-master.yaml")

        logging.info("Created RS in %s namespaces." %(namespace))
    except IOError as e:
        logging.error("Failed to create RS in %s namespaces: {}" %(namespace))
