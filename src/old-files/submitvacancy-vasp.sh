#!/bin/bash

# Check if a directory is provided, otherwise use the current directory
search_dir=${1:-.}

# Ensure vasp.sh exists in the head directory
if [[ ! -f "$search_dir/vasp.sh" ]]; then
    echo "Error: vasp.sh not found in $search_dir"
    exit 1
fi

# Find all directories named "VASP_inputs" and copy vasp.sh into them
#find "$search_dir" -type d -name "VASP_inputs" | while read -r dir; do
#    echo "Copying vasp.sh to $dir"
#    cp "$search_dir/vasp.sh" "$dir/"
#done

# Find all vasp.sh files in VASP_inputs directories and submit them
#find "$search_dir" -type f -name "vasp.sh" -path "*/VASP_inputs/*" | while read -r file; do
#    job_dir=$(dirname "$file")
 #   echo "Submitting sbatch in directory: $job_dir"
 #   (cd "$job_dir" && sbatch vasp.sh)
#done

# Find all directories named "VASP_inputs" and copy vasp.sh into them                                                                                                       
find "$search_dir" -type d -name "*_Pair*_Removed" | while read -r dir; do
    echo "Copying vasp.sh to $dir"
    cp "$search_dir/vasp.sh" "$dir/"
done


# Find all vasp.sh files in VASP_inputs directories and submit them                                                                                                         
find "$search_dir" -type f -name "vasp.sh" -path "*/*_Pair*_Removed/*" | while read -r file; do
    job_dir=$(dirname "$file")
    echo "Submitting sbatch in directory: $job_dir"
    (cd "$job_dir" && sbatch vasp.sh)
done

echo "All jobs submitted."
