#!/usr/bin/env python2
#-*- coding: UTF-8 -*-

import yaml
import logging
import os
import sys

def get_nodes_name():
    
    cpu_nodes = ""
    gpu_nodes = ""
    # cpu
    for i in range(1, int(cpu_num) + 1):
        cpu_svcName = ''.join(['pod-svc-ps', str(i)])
        cpu_nodes += cpu_svcName + "." + namespace + ".svc.cluster.local:2222"
        if not i == int(cpu_num):
            cpu_nodes += ","
    # gpu
    for i in range(1, int(gpu_num) + 1):
        gpu_svcName = ''.join(['pod-svc-worker', str(i)])
        gpu_nodes += gpu_svcName + "." + namespace + ".svc.cluster.local:2222"
        if not i == int(gpu_num):
            gpu_nodes += ","
    
    return cpu_nodes,gpu_nodes

def generate_service_template(serviceName, selectorName):

    py_object = {
                'apiVersion':'v1',
                'kind':'Service',
                'metadata':{'name':serviceName,'namespace':namespace},
                'spec':{'selector':{'run':selectorName},'ports':[{'name':'ssh','protocol':'TCP','port':22,'targetPort':22},{'name':'tf','protocol':'TCP','port':2222,'target':2222}]}
                }

    return py_object

def generate_gpu_pod_worker(num, yaml_file):

    list_arg_pod = []
    
    # generate svc
    svcName = ''.join(['pod-svc-worker', str(num)])
    svcSelector = ''.join(['pod-selector-worker', str(num)])
    py_object_svc = generate_service_template(svcName, svcSelector)

    #generate pod
    arg_pod = arg_base
    arg_pod += ' --jobname="worker" --taskindex=' + str(num - 1) + " > tf_result" + str(num - 1) + "; tail -f /dev/null;"
    list_arg_pod.append(arg_pod)
    podName = ''.join(['pod-worker', str(num)])
    containerName = ''.join(['pod-container-worker', str(num)])
    mount_path = "/usr/share/horovod"
    volume_name = "volume-name"
    claim_name = "pod-pvc-volume-1"
    py_object = {
                'apiVersion':'v1',
                'kind':'Pod',
                'metadata':{'name':podName,'namespace':namespace,'labels':{'run':svcSelector}},
                'spec':{'containers':[{'name':containerName,'image':image_name,'command':['/bin/sh','-c'],'args':list_arg_pod,'resources':{'limits':{'nvidia.com/gpu':1}},'volumeMounts':[{'name':volume_name,'mountPath':mount_path}]}],'volumes':[{'name':volume_name,'persistentVolumeClaim':{'claimName':claim_name}}]}}

    file = open(yaml_file, 'w')
    yaml.dump_all([py_object_svc, py_object], file)
    file.close()

def generate_cpu_pod_ps(num, yaml_file):

    list_arg_pod = []

    # generate svc
    svcName = ''.join(['pod-svc-ps', str(num)])
    svcSelector = ''.join(['pod-selector-ps', str(num)])
    py_object_svc = generate_service_template(svcName, svcSelector)

    #generate pod
    arg_pod = arg_base
    arg_pod += ' --jobname="ps" --taskindex=' + str(num - 1) + ";tail -f /dev/null;"
    list_arg_pod.append(arg_pod)
    podName = ''.join(['pod-ps', str(num)])
    containerName = ''.join(['pod-container-ps', str(num)])
    mount_path = "/usr/share/horovod"
    volume_name = "volume-name"
    claim_name = "pod-pvc-volume-1"
    py_object = {
                'apiVersion':'v1',
                'kind':'Pod',
                'metadata':{'name':podName,'namespace':namespace,'labels':{'run':svcSelector}},
                'spec':{'containers':[{'name':containerName,'image':image_name,'command':['/bin/sh','-c'],'args':list_arg_pod,'volumeMounts':[{'name':volume_name,'mountPath':mount_path}]}],'volumes':[{'name':volume_name,'persistentVolumeClaim':{'claimName':claim_name}}]}}

    file = open(yaml_file, 'w')
    yaml.dump_all([py_object_svc, py_object], file)
    file.close()



if __name__ == '__main__':
    try:
        namespace = sys.argv[1]
        gpu_num = sys.argv[2] # this num stand by the number of GPU pods
        cpu_num = sys.argv[3] # this num stand by the number of CPU pods
        exec_true = sys.argv[4]

        # TODO:some paramaters can be modified
        image_name = 'okwrtdsh/anaconda3:tf-10.0-cudnn7'
        # base command
        arg_base = 'cd /usr/share/horovod/tensorflow_distributed/; python example.py '
        current_path = os.path.abspath(".")

        # 提前生成CPU:2222,CPU:2222 GPU:2222,GPU:2222
        # 得先确定svcname

        cpu_nodes_str, gpu_nodes_str = get_nodes_name()
        arg_base += cpu_nodes_str + " " + gpu_nodes_str

        for i in range(1, int(cpu_num) + 1):
            file_name = ''.join(['cpu-pod-ps', str(i), '.yaml'])
            yaml_path = os.path.join(current_path, file_name)
            if not os.path.exists(yaml_path):
                generate_cpu_pod_ps(i, yaml_path)
                print("%s created"%(yaml_path))
            else:
                print("%s already exists"%(yaml_path))
            if exec_true == "true":
                k8s_apply = "kubectl apply -f " + yaml_path
                os.system(k8s_apply)

        for i in range(1, int(gpu_num) + 1):
            file_name = ''.join(['gpu-pod-worker', str(i), '.yaml'])
            yaml_path = os.path.join(current_path, file_name)
            if not os.path.exists(yaml_path):
                generate_gpu_pod_worker(i, yaml_path)
                print("%s created"%(yaml_path))
            else:
                print("%s already exists"%(yaml_path))
            if exec_true == "true":
                k8s_apply = "kubectl apply -f " + yaml_path
                os.system(k8s_apply)

        logging.info("Created RS in %s namespaces." %(namespace))
    except IOError as e:
        logging.error("Failed to create RS in %s namespaces: {}" %(namespace))
