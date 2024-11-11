* This do-file calculates the bilateral distances between all selected locations
* For India map, written by Treb on October 14, 2014 updated by Sapta for replication 
* For replication on China map, written by Ke on Nov 8, 2024

* making bilateral dataset
clear
use "$dir_scratch/China_customs.dta"
	ren portcode custom_orig
	ren row row_orig
	ren col col_orig
	cross using "$dir_scratch/China_customs.dta"
	ren portcode custom_dest
	ren row row_dest
	ren col col_dest
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

* TODO: Might want to include the straight bilateral distance... (India project has this)