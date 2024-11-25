% This m-file calculates the distance between all districts using the
% various highway maps

% written by Treb on 10/14/14

% Updated by Ke on 11/9/24, for replicate on China. 
% Notice: 
%    1. coords are already in the row and column form
%       (rather than in lon and lat, used in the India project)
%    2. images are in gray scale


clear
clc

% set paths
setpath

% Loading the raw (geo-coded) maps
%    cd ..

% NOTE: in all of the maps, except for map with multiple types of roads, all
%       map pixel values are 250. (close to white, 255, in grayscale)

    % China outline (our image is in gray scale, already 2D matrix)
        china_data = imread(strcat(dir_data_raw,'China_outline.tif'));
        in_china = china_data~=0;

    % Filter rules
        pen_thickness = 5
        thicker_pen_filter = fspecial('disk',pen_thickness);
        size_filt = 0.025; % what percent of pixels have to be "on" to count an area as "on"

    % Ming Dynasty Road data
        roads_data = (imread(strcat(dir_data_raw,'China_road.tif')));

        % getting each type of road
            % On land are 250
                on_land = double(roads_data==250);
                on_land = imfilter(on_land,thicker_pen_filter,'replicate'); 
                on_land = on_land>0; % not sure why here does not apply size_filt
                on_land = on_land.*in_china;
                
            % Water ways are 125 (1-on_land => make sure on_land has the highest priority)
                water_way = double(roads_data==125);
                water_way = imfilter(water_way,thicker_pen_filter,'replicate'); 
                water_way = water_way>size_filt; 
                water_way = water_way.*in_china.*(1-on_land);        
                
            % Mixed roads are 50
                mixed_road = double(roads_data==50);
                mixed_road  = imfilter(mixed_road ,thicker_pen_filter,'replicate'); 
                mixed_road  = mixed_road >size_filt; 
                mixed_road  = mixed_road.*in_china.*(1-water_way-on_land);                  
                
    % River data
        river_data = (imread(strcat(dir_data_raw,'China_river.tif')));
            
        % All rivers are 250
            rivers = double(river_data==250);
            rivers = imfilter(rivers,thicker_pen_filter,'replicate'); 
            rivers = rivers>size_filt;
            rivers = rivers.*in_china.*(1-water_way-on_land-mixed_road);

    % aggregate roads and rivers
        ming_roads_rivers = (on_land + water_way + mixed_road + rivers)>0;

    % Sea data (actually not sea territory, but all sea area near China)
        sea_data = (imread(strcat(dir_data_raw,'China_sea.tif')));

        % No need to widen the coastline and should be outside the China outline
            sea = sea_data==0; % the sea area are 0, land = 250
            sea = sea.*(1-in_china);


%% Calculating distances
% cd 'Distance calculations'
cd(dir_structural)

% Converting to speed images
    speed_on_land = 7; % normally 5-10 km/hr
    speed_water_way = 7;
    speed_mixed_road = 7;
    speed_river = 6; % normally 5-7 km/hr
    speed_sea = 9; % normally 8-10 km/hr
    speed_china = 3; % assume normal people walk at 3km/hr
    speed_elsewhere = 0.1;
    
    % All roads
    % speed_img = on_land.*speed_on_land + water_way.*speed_water_way + mixed_road.*speed_mixed_road + rivers.*speed_river + sea.*speed_sea + (1-ming_roads_rivers).*in_china*speed_china + (1-in_china)*speed_elsewhere;
    
    % Exclude Sea
    speed_img = on_land.*speed_on_land + water_way.*speed_water_way + mixed_road.*speed_mixed_road + rivers.*speed_river + (1-ming_roads_rivers).*in_china*speed_china + (1-in_china)*speed_elsewhere;

% Get the locations' indeices on the matrix
    data_coor = load(strcat(dir_scratch,'coor.out')); % N x 4 matrix
    orig_pix = data_coor(:,1:2); % origin row & col
    dest_pix = data_coor(:,3:4); % destination row & col
        
%%% Estimating the cost via each mode of travel from every origin to every
%%% destination
    image_X = size(in_china,2);
    image_Y = size(in_china,1);

% Loading the program we use to calculate distance 
    getd = @(p)path(p,path);

    % accurate fast marching (for 2d)
        getd(strcat(dir_structural,'/FastMarching_version3b/code'));

        N = size(data_coor,1); % number of bilateral pairs
        [temp_coor,temp_IA,temp_IC] = unique(orig_pix,'rows');
        K = size(temp_coor,1)
        disp('calculating distances')
    
        % want to normalize units by width of country
            % in China project, the height and width of one pixel is close to 1km
            unit_norm = 1; 

            temp_dist = cell(K);
            
        %  parpool(30)  TODO: use parfor.
        % parfor i = 1:K % my computer seems having memory limitation to do parellel computing.
        for i = 1:K
            
            i

            % here are the coordinates 
                temp_orig_y_2 = temp_coor(i,1);
                temp_orig_x_2 = temp_coor(i,2);

            % Calculation: from origin to EVERY other points in the matrix.
                distances_img = msfm(unit_norm*ones(size(speed_img)).*speed_img, [temp_orig_y_2;temp_orig_x_2], true, true);    
            
            % saving the distances 
            % => get the current origin point idx in orig_pix -> use this idx to get the dest point info 
            %    -> use the info to get distance from distances_img
                temp_loc = find(orig_pix(:,1)==temp_coor(i,1) & orig_pix(:,2)==temp_coor(i,2)); % all destinations      
                temp_dist{i}=[temp_loc, distances_img(sub2ind(size(distances_img),dest_pix(temp_loc,1),dest_pix(temp_loc,2)))];
        end
        
        % putting the distances back into the the correct order
            dist_china = NaN(size(data_coor,1),1);
            for i=1:K
                loc_dist_pair = temp_dist{i};
                temp_loc = loc_dist_pair(:,1);
                dist_china(temp_loc) = loc_dist_pair(:,2);
            end
            
%% exporting the data to stata
    temp = [dist_china];
    filename = strcat(dir_data_primary,'bilateral_travel_time_China',data_version,'.out');
    save(filename,'temp','-ascii','-tabs')
    
disp('hi!')
    