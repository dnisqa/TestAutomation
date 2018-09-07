#!/bin/bash

getbuild="$(more SonicDeb9build.txt | xargs)"; echo $getbuild
build_ver=${getbuild##* }; echo $build_ver; export $build_ver