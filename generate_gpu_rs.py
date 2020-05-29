#!/usr/bin/env python2
#-*- coding: UTF-8 -*-

import yaml
import logging
import os
import sys

def generate_service_template(serviceName, selectorName):

    py_object = {
                'apiVersion':'v1',
                'kind':'Service',
                'metadata':{'name':serviceName,'namespace':namespace},
                'spec':{'selector':{'run':selectorName},'ports':[{'name':'ssh','protocol':'TCP','port':22,'targetPort':22}]}
                }

    return py_object

def generate_gpu_pod_slave(yaml_file, num):

    # generate service
    svcName = ''.join(['pod-svc-slave', str(num)])
    svcSelector = ''.join(['pod-selector-slave', str(num)])
    py_object_svc = generate_service_template(svcName, svcSelector)

    # generate pod
    podName = ''.join(['pod-slave', str(num)])
    containerName = ''.join(['pod-container-slave', str(num)])
    py_object = {
                'apiVersion':'v1',
                'kind':'Pod',
                'metadata':{'name':podName,'namespace':namespace,'labels':{'run':svcSelector}},
                'spec':{'containers':[{'name':containerName,'image':image_name,'command':commands,'args':arg,'resources':{'limits':{'nvidia.com/gpu':1}}}]}
                }
    
    # join
    file = open(yaml_file, 'w')
    yaml.dump_all([py_object_svc, py_object], file)
    file.close()


if __name__ == '__main__':
    try:
        namespace = sys.argv[1]
        gpu_num = sys.argv[2] # this num stand by the number of GPU pods

        # TODO:some paramaters can be modified
        image_name = "horovod/horovod:0.18.1-tf1.14.0-torch1.2.0-mxnet1.5.0-py3.6"
        commands = "[ \"/bin/sh\", \"-c\" ]"
        arg = "[ \"cd /usr/share/horovod/SSD-Tensorflow/;apt update -y;apt install ssh vim sshpass -y;echo root:admin123|chpasswd;tmp='PermitRootLogin yes';sed -i \\\"/^#PermitRootLogin/c$tmp\\\" /etc/ssh/sshd_config;/etc/init.d/ssh restart; tail -f /dev/null \"]"
        current_path = os.path.abspath(".")

        if gpu_num > 1:
            for i in range(1,int(gpu_num)):
                file_name = ''.join(['gpu-pod-slave', str(i), '.yaml'])
                yaml_path = os.path.join(current_path, file_name)
                generate_gpu_pod_slave(yaml_path, i)
                print("%s created"%(file_name))

        yaml_path = os.path.join(current_path, "gpu-job-master.yaml")
        #generate_gpu_pod_slave(yaml_path)
        #print("%s created"%("gpu-job-master.yaml"))

        logging.info("Created RS in %s namespaces." %(namespace))
    except IOError as e:
        logging.error("Failed to create RS in %s namespaces: {}" %(namespace))
