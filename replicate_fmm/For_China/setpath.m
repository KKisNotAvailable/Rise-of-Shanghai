
%% set paths
dir_root = "D:/User_Data/Desktop/研究資料/HWT/Rise of Shanghai/replicate_fmm/";
dir_data = strcat(dir_root,'Data/');
dir_data_primary = strcat(dir_data, 'primary/');
dir_data_raw = strcat(dir_data, 'raw/');
dir_data_secondary = strcat(dir_data, 'secondary/');
dir_scratch = strcat(dir_data, 'scratch/');
dir_figures = strcat(dir_root,'Figures/');
dir_tables = strcat(dir_root, 'Tables/');
dir_structural = strcat(dir_root, 'For_China/');

%% set parallel pool preferences on number of workers

parpool_workers = 6; %% was 20

%% set data version by date
data_version = "_081721";