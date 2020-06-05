#!/usr/bin/env bash

NAMESPACE="default"
GPU_NUM=0
CPU_NUM=0
MAX_GPU_NUM=3
DELETE=0
EXEC_TRUE=true
DISTRIBUTION=horovod

#
# usage:
# If you want to use 2 GPUs to do the trainning:
#	./main.sh -g 2
# If you want to specify the NAMESPACE with 3 GPUs to do the trainning:(default namespace will be use if without -n NAMESPACE)
#	./main.sh -n ai -g 3
# If you want to use 2 CPUs to do the trainning:
#	./main.sh -c 2
# If you want to specify the NAMESPACE with 3 CPUs to do the trainning:(default namespace will be use if without -n NAMESPACE)
#	./main.sh -n ai -c 2
# If you want to mix GPUs and CPUs:
#	./main.sh -n ai -g 2 -c 2
# If you only want create those RS files() instead of executing it:(default will execute)
#	./main.sh balabala -e False
# If you want to delete all RS in the NAMESPACE:(default is by default:))
#	./main.sh -D ai
#

function help_me() {
	echo "Usage: ./main.sh -n [namespace] -g [GPUNUM] -c [CPUNUM] -e [true/false] -D [NAMESPACE] -d [tensorflow/horovod]-h"
	echo "-h		This message."
	echo "-D [namespace]	Delete all RS in the specific NAMESPACE"
	echo "-n [namespace]	create NAMESPACE when create RS"
	echo "-g [GPUNUM]	trainning with GPUNUM GPUs, 0 is nothing to create"
	echo "-g [CPUNUM]	trainning with GPUNUM CPUs, 0 is nothing to create"
	echo "-e [true/false]	true(default) means it will create RS files and execute or without execution"
	echo "-d [horovod/tensorflow]	choose one distribution framework to use, horovod is by default"
}

function get_opts() {
	while getopts "hD:n:g:c:e:d:" option; do
		case $option in
			d)
				DISTRIBUTION=$OPTARG
				;;
			e)
				EXEC_TRUE=$OPTARG
				;;
			n)
				NAMESPACE=$OPTARG
				;;
			g)
				GPU_NUM=$OPTARG
				;;
			c)
				CPU_NUM=$OPTARG
				;;
			D)
				# Since the default NAMESPACE is 'default', and delete it by accident is very dangerous. so
				# the paramater is required.
				DELETE=1
				NAMESPACE=$OPTARG
				;;
			h)
				help_me
				exit 1
				;;
			*)
				help_me
				exit 1
				;;
		esac
	done

	# TODO: please modify this value
	if [ $GPU_NUM -gt $MAX_GPU_NUM ]; then
		echo "Only $MAX_GPU_NUM GPUs support"
		exit 2
	fi
}

function generate_horovod_rs_file() {
	if [ $GPU_NUM -gt 0 ]; then
		# use GPU
		if [ $CPU_NUM -gt 0 ]; then
			# use GPU and CPU
			./generate_horovod_gpu_rs.py $NAMESPACE $GPU_NUM  $EXEC_TRUE
			./generate_horovod_cpu_rs.py $NAMESPACE $CPU_NUM $EXEC_TRUE
		else
			# only GPU
			./generate_horovod_gpu_rs.py $NAMESPACE $GPU_NUM $EXEC_TRUE
		fi
	elif [ $CPU_NUM -gt 0 ]; then
		# use CPU without GPU
		./generate_horovod_cpu_rs.py $NAMESPACE $CPU_NUM $EXEC_TRUE
	else
		# nothing to create but namespace
		echo -e "\033[31mnothing to do except for namespace created !!\033[0m"
	fi
}

function generate_tensorflow_rs_file() {
	if [ $GPU_NUM -gt 0 ] && [ $CPU_NUM -gt 0 ]; then
		# GPU only be the worker
		./generate_tensorflow_rs.py $NAMESPACE $GPU_NUM $CPU_NUM $EXEC_TRUE
	else
		echo -e "\033[31mPS distribution specified 1 master(cpu) and 1 worker(gpu) at least\033[0m"
	fi
}

get_opts ${@}

if [ $DELETE -eq 1 ]; then
	kubectl delete job/job-master -n $NAMESPACE
	kubectl delete --all pods --namespace=$NAMESPACE	
	kubectl delete --all svc --namespace=$NAMESPACE	
#	kubectl delete namespace $NAMESPACE
	exit 0
fi

# create namespace
kubectl create namespace $NAMESPACE


case $DISTRIBUTION in
	horovod)
		echo -e "\033[36mStart generate YAML RS files...\033[0m"
		generate_horovod_rs_file
		;;
	tensorflow)
		echo -e "\033[36mStart generate YAML RS files...\033[0m"
		generate_tensorflow_rs_file
		;;
	*)
		echo -e "\033[31mWrong distribution framework support!!\033[0m"
		help_me	
		exit 1
		;;
esac
