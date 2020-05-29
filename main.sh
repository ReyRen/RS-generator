#!/usr/bin/env bash

NAMESPACE="default"
GPU_NUM=0
CPU_NUM=0
MAX_GPU_NUM=3


function help_me() {
	echo "Usage: ./main.sh -n [namespace] -g GPUNUM -c CPUNUM]"
	echo "-h	This message."
	echo "-D	Delete all balabala"
}

function get_opts() {
	while getopts "hDn:g:c:" option; do
		case $option in
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
				bala_DELETE=true
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

function generate_rs_file() {
	if [ $GPU_NUM -gt 0 ]; then
		# use GPU
		if [ $CPU_NUM -gt 0 ]; then
			# use GPU and CPU
			./generate_gpu_rs.py $NAMESPACE $GPU_NUM
			./generate_cpu_rs.py $NAMESPACE $CPU_NUM
		else
			# only GPU
			./generate_gpu_rs.py $NAMESPACE $GPU_NUM
		fi
	elif [ $CPU_NUM -gt 0 ]; then
		# use CPU without GPU
		./generate_cpu_rs.py $NAMESPACE $CPU_NUM
	else
		# nothing to create but namespace
		echo "nothing to do except for namespace created !!"
	fi
}

get_opts ${@}

# create namespace
kubectl create namespace $NAMESPACE

echo "Start generate YAML RS files..."
generate_rs_file
