* This do-file calculates the bilateral distances between all districts in each decade
* written by Treb on October 14, 2014
* Updated by Sapta for replication 

clear


use "$dir_scratch/ICRISAT_latlong_BiggestCity_${date}.dta" 
	ren State state
	ren District district
/* use "$dir_data_raw/district_geoloc.dta"
	ren latitude_google latitude
	ren longitude_google longitude
	* TAMIL NADU,CHENGALPATTU M.G.R. has empty set of coord, drop this row
	drop if missing(latitude) | missing(longitude) */

* Identifying all districts
	keep state district latitude longitude
	sort state district
	bysort state district: keep if _n==1
save "$dir_scratch/district_location_${date}.dta", replace

* making bilateral dataset
clear
use "$dir_scratch/district_location_${date}.dta"
	ren state state_orig
	ren district district_orig
	ren latitude latitude_orig
	ren longitude longitude_orig
	cross using "$dir_scratch/district_location_${date}.dta"
	ren state state_dest
	ren district district_dest
	ren latitude latitude_dest
	ren longitude longitude_dest
	sort state_orig district_orig state_dest district_dest
	lab dat "Bilateral distances"
save "$dir_scratch/district_distance_${date}.dta", replace

* outsheet the distances to matlab
outsheet longitude_orig latitude_orig longitude_dest latitude_dest using "$dir_scratch/coor.out", noname nol replace 

* If highway distances are to be recalculated, set flag = 1 (details in README)
	if `redo_highwaydistance' == 1{
		shell matlab -batch "distance_081721" > matlab_output.log 2>&1
	}
		
cd "$dir"	
* merging on Matlab generated distances
foreach d in 5 10 15 20 30 {
	
clear
insheet using "$dir_data_primary/distances_offhighwayspeed`d'_${date}.out", tab
	ren v1 distance_1962
	ren v2 distance_1969
	ren v3 distance_1977
	ren v4 distance_1988
	ren v5 distance_1996
	ren v6 distance_2004
	ren v7 distance_2011
	drop v*
	gen temp = _n
	sort temp
	tempfile temp
save `temp', replace
	
clear
use "$dir_scratch/district_distance_${date}.dta"
	cap drop distance*
	cap drop temp*
	gen temp = _n
	sort temp
	merge temp using `temp'
	tab _merge
	drop _merge
	drop temp
	sort state_orig district_orig state_dest district_dest
	
* checking that the distances make sense
	vincenty latitude_orig longitude_orig latitude_dest longitude_dest, vin(distance_straight)
	corr distance* /* looks good */
	sum distance*
		
* saving
	lab var distance_1962 "Distance (in hours) between locations using roads in 1962"
	lab var distance_1969 "Distance (in hours) between locations using roads in 1969"
	lab var distance_1977 "Distance (in hours) between locations using roads in 1977"
	lab var distance_1988 "Distance (in hours) between locations using roads in 1988"
	lab var distance_1996 "Distance (in hours) between locations using roads in 1996"
	lab var distance_2004 "Distance (in hours) between locations using roads in 2004"
	lab var distance_2011 "Distance (in hours) between locations using roads in 2011"
	lab var distance_straight "Straightline distance between locations (in miles)"
	sort state_orig district_orig state_dest district_dest
	order state_orig district_orig state_dest district_dest latitude_orig longitude_orig latitude_dest longitude_dest distance*
	lab dat "Bilateral distances"
save "$dir_data_primary/district_distance_dist`d'_${date}.dta", replace
		
}
	
		
		
		
		
		
		
		


