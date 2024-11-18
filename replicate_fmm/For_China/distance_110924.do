* This do-file calculates the bilateral distances between all selected locations
* For India map, written by Treb on October 14, 2014 updated by Sapta for replication 
* For replication on China map, written by Ke on Nov 8, 2024

* making bilateral dataset
clear
use "$dir_scratch/China_customs.dta"
	ren portcode custom_orig
	ren row row_orig
	ren col col_orig
	ren lon lon_orig
	ren lat lat_orig
	cross using "$dir_scratch/China_customs.dta"
	ren portcode custom_dest
	ren row row_dest
	ren col col_dest
	ren lon lon_dest
	ren lat lat_dest
	lab var custom_orig "self defined portcode - starting point"
	lab var custom_dest "self defined portcode - destination"
	lab var row_orig "row index in the matrix - starting point"
	lab var col_orig "col index in the matrix - starting point"
	lab var lon_orig "longtitude - starting point"
	lab var lat_orig "latitude - starting point"
	lab var row_dest "row index in the matrix - destination"
	lab var col_dest "col index in the matrix - destination"
	lab var lon_dest "longtitude - destination"
	lab var lat_dest "latitude - destination"
	sort custom_orig custom_dest
	lab dat "Bilateral distances"
save "$dir_scratch/custom_distance_${date}.dta", replace

* outsheet the distances to matlab
outsheet row_orig col_orig row_dest col_dest using "$dir_scratch/coor.out", noname nol replace 

* If highway distances are to be recalculated, set flag = 1 (details in README)
	if `redo_highwaydistance' == 1{
		shell matlab -batch "distance_110924" > matlab_output.log 2>&1
	}
	* generates 'bilateral_travel_time_China_110924.out'

* Compare calculated distance with the straight distance
clear
insheet using "$dir_data_primary/bilateral_travel_time_China_${date}.out", tab
	ren v1 distance_calculated
	drop v*
	gen temp = _n
	sort temp
	tempfile temp
save `temp', replace

clear
use "$dir_scratch/custom_distance_${date}.dta"
	cap drop distance* // follows the original code, but I don't think it's necessary
	cap drop temp* // follows the original code, but I don't think it's necessary
	gen temp = _n
	sort temp
	merge temp using `temp'
	tab _merge
	drop _merge
	drop temp
	sort custom_orig custom_dest
	
    * get the pairwise straight line distance
	vincenty lat_orig lon_orig lat_dest lon_dest, vin(distance_straight) inkm
	lab var distance_calculated "calculated travel time (hr)"
	lab var distance_straight "straight distance (km)"
	corr distance* /* looks good */
	sum distance*
save "$dir_data_primary/final_result_${date}.dta", replace
