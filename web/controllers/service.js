		
angular.module('sam').controller('serviceController', ['$scope', '$filter','$http','$log', '$location','$compile', '$routeParams', '$modal', 'User', 'ngTableParams', function($scope, $filter, $http, $log, $location, $compile, $routeParams, $modal, User, ngTableParams) {
	
	this.availableServiceRequests = [];	
	
	tmp = this;
	//a factory which passes paramteres cross controllers
	this.user = User;	
	if (_.contains(_.keys($routeParams), 'client_id')){
		$log.log('yes there is');
		this.user.setNavBarHidden(true);
	}
	
	this.maximum_records = 0;
	this.limit = 25;
	
	if (_.isUndefined(this.user.start_dt)) {
		//start at the first day of the year at midnight and 1 minute and 16 seconds
		this.user.start_dt = new Date(new Date().getFullYear() - 1, 0, 1, 16);
	}
	
	if (_.isUndefined(this.user.finish_dt)) {
		//end date defaults for today
		this.user.finish_dt = new Date();	
	}
	
	this.buildingData = "";
	this.tenantData = "";	
	this.professionalData = "";
		
	this.serviceData = {};	
	this.showAddForm = false;	
	this.loading = false;	
	
	this.statusOf = {1: 'פתוח', 2:'בעבודה', 3: 'סגור'};
	this.statusesWithIdle = [{status: 0, desc: 'הצג קריאות שירות בכל סטטוס'}, {status: 4, desc:' הצג קריאות שירות פעילות (פתוחות או סגורות)'}, {status: 5,desc: 'הצג קריאות שדורשות טיפול (פעילות מעל 14 ימים)'}, {status: 1,desc: 'הצג קריאות שירות פתוחות'}, {status: 2, desc: 'הצג קריאות שירות בעבודה'}, {status: 3, desc:'הצג קריאות שירות סגורות'}]
	this.serviceType = [{status: 0, desc: 'הצג קריאות שירות מכל הסוגים'}, {status: 1,desc: 'הצג קריאות שירות שוטפות'}, {status: 2, desc: 'הצג טיפולים מונעים'}]
	this.filterStatus = this.statusesWithIdle[0];
	this.filterType = this.serviceType[0];

	this.openTime = new Date();
	this.closeTime = new Date();	
	
	this.column_id = true;
	this.column_status = true;
	this.column_description = true;
	this.column_category = true;
	this.column_building = true;
	this.column_tenant = true;
	this.column_worker = true;
	this.column_professional = true;
	this.column_start_date = true;
	this.column_end_date = true;
	this.column_comment = true;
	this.column_cost = false;
	
	this.masterCheckBoxState = 1; //1- uncheck, 2-partial, 3-all		
	this.total_services = 0;
	this.showColumnPanel = false;
	
	this.availableTenants = [];
	this.tableParams = new ngTableParams(
		{
			//initial sorting by a decreasing date
			sorting: {start_date: "desc"}               
		},
		{
			counts: [],		
			total: this.availableServiceRequests.length, // length of data
			getData: function($defer, params) {				
				var orderedData = tmp.orderData(tmp.availableServiceRequests);							

				//$defer.resolve(orderedData);
				tmp.availableServiceRequests = orderedData;
			}
		}
	);
		
	this.orderData = function(data) {
						
		params = this.tableParams;		
		var objectOf = null;
		var key = null;
		var direction = null;
		
		if (params.sorting().building_name) {	
			key = "building_id";
			objectOf = this.serviceData.buildingObjectPerBuildingId;
			direction = params.sorting().building_name;
		}
		else if (params.sorting().tenant_name) {	
			key = "tenant_id";
			objectOf = this.serviceData.tenantObjectPerTenantId;
			direction = params.sorting().tenant_name;
		}
		else if (params.sorting().worker_name) {	
			key = "worker_id";
			objectOf = this.workerOf;
			direction = params.sorting().worker_name;
		}
		else if (params.sorting().professional_name) {	
			key = "professional_id";
			objectOf = this.professionalOf;
			direction = params.sorting().professional_name;
		}
				
		//http://stackoverflow.com/questions/26045390/ng-table-how-to-sort-by-a-value-which-is-not-a-part-of-ng-repeat
		if (key && objectOf && direction) {
			orderedData = data.sort(function(a, b){				
				
				//a key could not exist or point to non existing object (for example a building which were deleted)
				var nameA = a[key] == "" || _.isUndefined(objectOf[a[key]]) ? "" : objectOf[a[key]].name.toLowerCase();
				var nameB = b[key] == "" || _.isUndefined(objectOf[b[key]]) ? "" : objectOf[b[key]].name.toLowerCase();				
				
				if (nameA < nameB)
					return -1;
					
				if (nameA > nameB)
					return 1;
				
				return 0 ;
			});
			
			if (direction == 'desc') {
			  orderedData = orderedData.reverse();
			}
		}
		
		else {
			var orderedData = params.sorting() ?
										$filter('orderBy')(data, params.orderBy()) :
										data;
		}
		
		return orderedData;
		
	}	
	
	this.addNewServiceRequest = function(){		
		tmp = this;	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		
		$http.post('/addNewServiceRequest', 
			$.param({
				service_request: JSON.stringify(this.session)			
			}
			)).success(function(data) {				
				tmp.loading = false; 
				tmp.showAddForm = false;
				tmp.session = {};	
				tmp.GetServiceRequests(data.service_request_id);				
		});
	};
	
	this.UpdateBuildingTenants = function(){
		tmp = this;				
						
		//if building is null, give all options for tenants
		if (!this.session.building_id){			
			this.availableTenants = _.map(_.flatten(_.values(this.serviceData.tenantsIdsPerBuildingId) ),
											function(tenantId){												
												return tmp.serviceData.tenantObjectPerTenantId[tenantId]; 
												});
		}
		//list tenant from chosen building
		else {
			this.availableTenants = _.map(this.serviceData.tenantsIdsPerBuildingId[this.session.building_id], 
											function(tenantId){												
												return tmp.serviceData.tenantObjectPerTenantId[tenantId]; 
												});			
		}
	};
	
	this.UpdateTenantBuilding = function(){				
		//if no building picked, update the building id of this tenant
		if (!this.session.building_id && this.session.tenant_id){
			this.session.building_id = this.serviceData.buildingIdPerTenantId[this.session.tenant_id];			
		}
	};
	
	this.ClearBuilding = function(){	
		this.session.building_id = null;		
	};
	
	this.AutoCompleteChange = function(val) {				
		if(val == "") {
			this.GetServiceRequests();
		}						
	};
		
		
	this.GetServiceData = function(){			
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchServiceData', {
		}).success(function(data) {
				
				tmp.serviceData = data;
				tmp.availableBuildings = _.values(data.buildingObjectPerBuildingId);
				tmp.UpdateBuildingTenants();
				tmp.UpdateTenantBuilding();
				tmp.service_sla = data.service_sla;
				tmp.loading = false;				
		});
	};
	
	
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	};
				
			
	this.open_start = function($event) {			
		$event.preventDefault();
		$event.stopPropagation();

		this.opened_start = true;
	 };
	 
	this.open_end = function($event) {
		$event.preventDefault();
		$event.stopPropagation();

		this.opened_end = true;
	};
	 
	this.masterCheckBoxClick = function($event){		
		if (this.masterCheckBoxState == 1){			
			this.selectAll();
		}
		else if (this.masterCheckBoxState == 3){			
			this.clearSelections();	
		}
		else if (this.masterCheckBoxState == 2){			
			this.clearSelections();	
		}
		$event.stopPropagation();		
	};
	
	this.clearSelections = function(){											
		tmp = this;
		angular.forEach(this.availableServiceRequests, function(data, index){							
			data.service_selected = false;			
		});
	};
	
	this.selectAll = function(){							
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.availableServiceRequests, function(data, index){							
			data.service_selected = true;			
		});
	};
	
	this.selectServiceByStatus = function(status){
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.availableServiceRequests, function(data, index){			
			if(data.status == status){				
				data.service_selected = true;				
			}
		});
	};
	
	this.guessBuildingName = function(val) {		
		return $http.get('/guessBuilding', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};
	
	//call server to get all professionals' info
	this.GetProfessionals = function(updated_professional){		
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp = this;			
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchProfessionals', {
		params: {		
			updated_professional: updated_professional,
			start_date: $filter('date')(tmp.user.start_dt, 'yyyy-MM-dd' ),
			end_date: $filter('date')(tmp.user.finish_dt, 'yyyy-MM-dd')
		}
		}).success(function(data) {						
			tmp.professionalOf = data.professionals;
			tmp.availableProfessionals = _.values(tmp.professionalOf);						
			tmp.loading = false;						
		});
	};		
	
	//call server to get all Workers' info
	this.GetWorkers = function(){		
		tmp = this;	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchWorkers', {
		params: {}
		}).success(function(data) {			
			tmp.workerOf = data.workers;
			tmp.availableWorkers = _.values(tmp.workerOf);			
			
			tmp.loading = false;						
		});
	};
	
	this.UpdateServicesMetaData = function(delta) {
		this.total_services += delta;
		if (!this.total_services) {
				this.masterCheckBoxState = 1;
			}
		else if (this.total_services == _.keys(services_data).length) {
			this.masterCheckBoxState = 3;
		}
		else {
			this.masterCheckBoxState = 2;
		}						
	};		
	
	this.UpdateServiceRequests = function(new_services) {
		tmp = this;				
		tmp.total_services = 0;
		services_data = tmp.orderData(new_services);		
		
		//remove previous watches
		angular.forEach(tmp.availableServiceRequests, function(service, index){
			service['listener']();
		});								
		
		angular.forEach(services_data, function(service, index){
			//when fetching the services_data, each row which is selected from the beginning will not
			if (services_data[index].service_selected) {				
				tmp.UpdateServicesMetaData(1);				
			}
			
			
			//add watchers for all services to track changes in row selections (this is due to the fact that angular does not 
			//trigget on change methods when model is changed)				
			listener = $scope.$watch(
			//watchExpression
			function(){
				return services_data[index];
			}, 
			//listener
			function(nv, ov) {				
				//row check box has changed
				if (nv.service_selected != ov.service_selected) {					
					//update total of services selected
					delta = 1;
					if (!nv.service_selected) {
						delta *= -1;
					}		
					
					tmp.UpdateServicesMetaData(delta);
				}
			},
			//objectEquality
			true);	
			
			//http://stackoverflow.com/questions/14957614/angular-js-clear-watch
			//store the return value from each watch. this is the function which deregister the object
			service['listener'] = listener;
		});
		
		tmp.availableServiceRequests = services_data;			
		tmp.loading = false;		
	}

	
	//call server to get all service Requests' info
	this.GetServiceRequests = function(service_request_id, building_id_input, tenant_id_input, worker_id_input, professional_id_input, showmore){		
		if (!showmore) {
			this.limit = 25;
		}
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp = this;		
		
		tmp.masterCheckBoxState = 1;		
		tmp.loading = true; 
		tmp.clearSelections();
		
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchServiceRequests', {
		params: {
			updated_service_request_id: service_request_id,
			status: tmp.filterStatus.status,
			service_type: tmp.filterType.status,
			building_id: tmp.buildingData.id,
			tenant_id: tmp.tenantData.id,			
			professional_id: tmp.professionalData.id,
			start_date: $filter('date')(tmp.user.start_dt, 'yyyy-MM-dd' ),
			end_date: $filter('date')(tmp.user.finish_dt, 'yyyy-MM-dd'),
			limit: tmp.limit
		}
		}).success(function(data) {					
			tmp.maximum_records = data.maximum_records;	
			tmp.UpdateServiceRequests(_.values(data.service_requests));				
			
			edit = false;
			if (!_.isUndefined(building_id_input) && building_id_input.length) {				
				tmp.session.building_id = building_id_input;
				edit = true;
			}
			
			if (!_.isUndefined(tenant_id_input) && tenant_id_input.length) {				
				tmp.session.tenant_id = tenant_id_input;
				edit = true;
			}
			
			if (!_.isUndefined(worker_id_input) && worker_id_input.length) {				
				tmp.session.worker_id = worker_id_input;
				edit = true;
			}
			
			if (!_.isUndefined(professional_id_input) && professional_id_input.length) {				
				tmp.session.professional_id = professional_id_input;
				edit = true;
			}
			
			if (edit == true) {				
				tmp.showAddForm = true;
			}
			else {
				tmp.showAddForm = false;
			}
			
		});
				
		
	};
	
	this.editServiceRequest = function(service_details) {		
		this.showAddForm = true;	
		this.session = service_details;	
		$log.log(service_details);
		this.session.status = String(this.session.status);				
		
		this.UpdateBuildingTenants();							
		
		this.session.edit = true;		
	};
	
	this.deleteServiceRequests = function(row) {
		if (confirm('אשר מחיקת קריאות שירות') ) {
			tmp = this;
			chosenServices = [];
			chosenPreventions = [];

			if (row) {
				service_id = row.service_id;
				chosenServices = [service_id];

				if (row.prevention_id) {
                    chosenPreventions.push(row.prevention_id);
                }
			}
			else {				
				$.each(this.availableServiceRequests, function(index, data){
					if (data.service_selected) {
						chosenServices.push(data.service_id);
					}
					if (data.prevention_id) {
						chosenPreventions.push(data.prevention_id);
					}
				});
			}

			tmp.deleteServicePreventionPopUp(chosenServices, chosenPreventions);
		}
							
	};
	
	this.multipleServiceReminders = function() {	
		tmp = this;
		chosenServices = [];
		$.each(this.availableServiceRequests, function(index, data){
			//choose only service requests which have building and professional assigned 
			if (data.service_selected && data.building_id && data.professional_id) {			
				chosenServices.push(data.service_id);
			}				
		});		 			
		
		if (!chosenServices.length) {
			alert("לא נמצאו קריאות שירות עם בנין ואיש מקצוע משוייכים");
			return;
		}
		
		var modalInstance = $modal.open({
			  templateUrl: 'myMultipleServiceReminderModalContent.html',
			  controller: 'multipleReminderCtrl',			  
			  //this passes the main scope status to the controller one
			  resolve: {				
				service_requests: function () {
					return chosenServices;
				},
				workers: function () {
					return tmp.availableWorkers;
				}
			  }
			});
			
			modalInstance.result.then(function (smsDetails) {				
				tmp.sendServiceReminders(smsDetails.service_requests, smsDetails.worker_id);
			}, function () {
			  $log.info('Modal dismissed at: ' + new Date());
			});
	};
	
	this.sendServiceReminders = function(chosenServices, worker_id){
		tmp.loading = true;
		$http.post('/sendServiceReminders', 
		$.param(
			{
				path: 'web\\customer_templates\\service_reminder',
				'service_ids': JSON.stringify(chosenServices),
				'worker_id': worker_id
			}
		)).success(function(data) {				
			tmp.loading = false;
			tmp.GetServiceRequests();
		}).error(function(data) {
			console.log('response: ',data);
		});
	}
								
		
	this.updateServiceRequest = function(service_details) {
		tmp = this;	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		
		$http.post('/updateServiceRequest', 
			$.param({
				service_request: JSON.stringify(service_details)			
			}
			)).success(function(data) {				
				tmp.loading = false;			
		});
	};	
	
	this.updateServiceRequestStatus = function(service_details) {		
		if (service_details.status == 1) {			
			service_details.end_date = "";
			var now = new Date();
			
			//http://stackoverflow.com/questions/1957000/how-to-get-current-time-in-the-format-2009-12-24-142057-in-javascript
			var pretty = [
				now.getFullYear(),
				'-',
				((now.getMonth() + 1)<10?'0':'') + (now.getMonth() + 1),
				'-',
				(now.getDate()<10?'0':'') + now.getDate(),
				' ',
				(now.getHours()<10?'0':'') + now.getHours(),
				':',
				(now.getMinutes()<10?'0':'') + now.getMinutes(),
				':',
				(now.getSeconds()<10?'0':'') + now.getSeconds()
			].join('');
			
			service_details.start_date =  pretty;
		}
		else if (service_details.status == 2) {			
			service_details.end_date = "";
		}
		else if (service_details.status == 3) {			
			var now = new Date();
			
			//http://stackoverflow.com/questions/1957000/how-to-get-current-time-in-the-format-2009-12-24-142057-in-javascript
			var pretty = [
				now.getFullYear(),
				'-',
				((now.getMonth() + 1)<10?'0':'') + (now.getMonth() + 1),
				'-',
				(now.getDate()<10?'0':'') + now.getDate(),
				' ',
				(now.getHours()<10?'0':'') + now.getHours(),
				':',
				(now.getMinutes()<10?'0':'') + now.getMinutes(),
				':',
				(now.getSeconds()<10?'0':'') + now.getSeconds()
			].join('');
			
			service_details.end_date =  pretty;
		}
		
		service_details.edit = true;
		this.session = service_details;
		this.addNewServiceRequest();
		
		//after service has been updated, time to send reminder
		//this.serviceReminder(service_details);
	};
	
	this.serviceReminder = function(service_details, recepient_id, status, template) {		
		if (!service_details.professional_id) {
			alert("על מנת לשלוח תזכורת לבעל מקצוע יש לוודא כי הקריאה מכילה נתונים על בעל מקצוע ");
		}
		else {		
			this.serviceReminderPopUp(service_details, recepient_id, status, template);
		}
	};
	
	this.serviceReminderTenant = function(service_details, recepient_id, status, template) {		
		if (!service_details.tenant_id) {
			alert("על מנת לשלוח תזכורת לדייר יש לוודא כי הקריאה מכילה נתונים על דייר");
		}
		else {		
			this.serviceReminderPopUp(service_details, recepient_id, status, template);
		}
	};
	
	this.serviceReminderPopUp = function (row, recepient_id, status, template) {
		focal_points = [];
		tmp = this;
		this.row_to_change = row;

		//if no sms to professional, do nothing
		if (false) {
			return;
		}

		if (row.building_id) {
			building_name = tmp.serviceData.buildingObjectPerBuildingId[row.building_id].name;
			tenantsPerBuilding = tmp.serviceData.tenantsIdsPerBuildingId[row.building_id];

			//fetch focal points for this building
			angular.forEach(tenantsPerBuilding, function(data, index){
			    tenantObj = tmp.serviceData.tenantObjectPerTenantId[data];
			    if (tenantObj.focal_point){
			        focal_points.push(tmp.serviceData.tenantObjectPerTenantId[data]);
			    }
            });
		}

		else {
			building_name = "";
		}

        //if there are several focal points in a building, take the first one for now. Maybe in the future, we will add some
        //support for a message which takes into account multiple focal points
		if (focal_points.length){
		    msg = 'אשר כי הודעת ל' + focal_points[0].tenant_name + ' על יצירת קשר עם בעל המקצוע' + "\n" + 'ניתן ליצור קשר ב: ' + focal_points[0].tenant_phones;
		    //check if the
		    if (!confirm(msg)){
		        return;
		    }
		}

		if (row.tenant_id) {
			tenant_name = tmp.serviceData.tenantObjectPerTenantId[row.tenant_id].tenant_name;
			tenant_phones = tmp.serviceData.tenantObjectPerTenantId[row.tenant_id].tenant_phones.replace(',', ' ');
			//replace , with space, so it will be apresented as a valid link in the iphone
		}
		else {
			tenant_name = "";
			tenant_phones = "";
		}
		if (row.professional_id) {
			professional_name = tmp.professionalOf[row.professional_id].name;
		}
		else {
			professional_name = "";
		}
		if (row.worker_id) {
			worker_name = tmp.workerOf[row.worker_id].name;
		}
		else {
			worker_name = "";
		}

		/*
		here to put if according to reminder (tenant/professional) and to service status and to update profId
			*/
		$http.get('/getServiceReminderData', {
		params: {			
			path: 'web\\customer_templates\\'+template,				
			details: JSON.stringify({
				//only service request description and id will exist for sure, the rest are optional 
				'service_request_description': row.description,
				'service_request_id': row.service_id,
				'building': building_name,
				'professional_name': professional_name,
				'worker_name': worker_name,
				'tenant_name': tenant_name,
				'tenant_phones': tenant_phones
			}),
			alert: 'sms',
			tenants_from_building_id: row.building_id
		}
		}).success(function(data) {				
			tmp.sms_content = data.content;
			tmp.sms_meta = data.meta;
			/*
			here to put if according to reminder (tenant/professional) and to service status and to update profId
			*/
			//profId = 'professional-'+row.professional_id;
			$log.log('recepient_id', recepient_id);
			tmp.chosenEntities = [recepient_id];	
			tmp.worker_id = row.worker_id;
			tmp.building_entities = data.entities;			
			
			var modalInstance = $modal.open({
			  templateUrl: 'myServiceReminderModalContent.html',
			  controller: 'reminderCtrl',			  
			  //this passes the main scope status to the controller one
			  resolve: {				
				building_name: function () {
					return building_name;
				},
				tenant_name: function () {
					return tenant_name;
				},
				worker_name: function () {
					return worker_name;
				},
				professional_name: function () {
					return professional_name;
				},
				entities: function () {
					return tmp.building_entities;
				},
				chosenEntities: function () {
					return tmp.chosenEntities;
				},
				sms_content: function () {
					return tmp.sms_content;
				},
				service_request: function () {
					return row;
				},
				workers: function () {
					return tmp.availableWorkers;
				},
				worker_id: function () {
					return tmp.worker_id;
				},
			  }
			});
			
			modalInstance.result.then(function (smsDetails) {				
				tmp.sendGroupSms(smsDetails.chosenEntities, smsDetails.sms_content, smsDetails.worker_id, smsDetails.building_name, smsDetails.service_id);
			}, function () {
			  $log.info('Modal dismissed at: ' + new Date());
			});
		}).
		error(function(data) {
			$log.log('error: ',date);
		});
		
		
		
	};
	
	// Any function returning a promise object can be used to load values asynchronously
	this.guessBuildingName = function(val) {		
		return $http.get('/guessBuilding', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};
	
	// Any function returning a promise object can be used to load values asynchronously
	this.guessTenantName = function(val) {		
		return $http.get('/guessTenant', {
			params: {
			name: val,
			building_id: this.buildingData.id
			}
		}).then(function(res) {		
			return res.data;
		});
	};
	
	// Any function returning a promise object can be used to load values asynchronously
	this.guessProfessional = function(val) {		
		return $http.get('/guessProfessional', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};
	
	this.changeStatus = function(row, new_status) {
		this.changeStatusPopUp(row, new_status);
	};
		
	this.changeStatusPopUp = function (row, new_status) {
		
		tmp = this;
		this.row_to_change = row;
		this.new_status_to_apply = new_status;
				
		//if same status is chosen, ignore
		if (new_status == row.status) {
			return;
		}
				
		var modalInstance = $modal.open({
		  templateUrl: 'myConfirmationModalContent.html',
		  controller: 'confirmationCtrl',	
		  //this passes the main scope status to the controller one
		  resolve: {
			service_request: function () {
			  return row;
			},
			new_status: function () {
			  return tmp.statusOf[new_status];
			}
		  }
		});
		
		modalInstance.result.then(function () {						
			tmp.row_to_change.status = tmp.new_status_to_apply; 
			tmp.updateServiceRequestStatus(tmp.row_to_change);				  
		}, function () {
		  $log.info('Modal dismissed at: ' + new Date());
		});
	};

	this.deleteServicePreventionPopUp = function (chosenServices, chosenPreventions) {

		tmp = this;
        if (chosenPreventions.length) {
            var modalInstance = $modal.open({
              templateUrl: 'myServicePreventionModalContent.html',
              controller: 'servicePreventionModalCtrl',
              resolve: {}
            });

            modalInstance.result.then(function (delete_status) {
                tmp.deleteServiceRequestsFromServer(chosenServices, chosenPreventions, delete_status);
            }, function () {
              tmp.delete_status = -1;
              $log.info('Modal dismissed at: ' + new Date());
            });

         }
         else {
            tmp.deleteServiceRequestsFromServer(chosenServices, chosenPreventions, 0);
         }
	};

	this.deleteServiceRequestsFromServer = function(chosenServices, chosenPreventions, delete_status) {
        tmp.loading = true;
        $http.post('/deleteServiceRequests',
        $.param(
            {
                'service_ids': JSON.stringify(chosenServices),
                'prevention_ids': JSON.stringify(chosenPreventions),
                'delete_status': delete_status
            }
        )).success(function(data) {
            tmp.loading = false;
            tmp.GetServiceRequests();
        }).error(function(data) {
            console.log('response: ',data);
        });
	};
	
	this.MultiTypeElements = function(){			
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchMultiTypeElements', {
		params: {		
			include_specific_buildings: true			
		}
		}).success(function(data) {	
				tmp.entities = data.entities;				
				tmp.loading = false;				
		});
	};
	
	this.sendGroupSms = function(chosenEntities, sms_content, worker_id, building_name, service_request_id){
		
		tmp.loading = true;		
				
		$http.get('/sendGroupSms', {
		params: {		
			recepients: JSON.stringify(chosenEntities),
			sms_body: sms_content,
			worker_id: worker_id,
			building_name: building_name
		}
		}).success(function(data) {				
			tmp.loading = false;
			tmp.IncreaseServiceReminders(service_request_id);			
			//update badge
		}).
		error(function(data) {
			
		});
	};	

	this.IncreaseServiceReminders = function(service_request_id){
		
		tmp.loading = true;		
				
		$http.get('/increaseServiceReminders', {
		params: {		
			service_request_id: service_request_id
		}
		}).success(function(data) {				
			tmp.loading = false;
			tmp.GetServiceRequests(service_request_id);			
		}).
		error(function(data) {
			
		});
	};	
	
	this.guessServiceCategory = function(val) {		
		return $http.get('/guessServiceCategory', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};
	
	this.ChangeMultipleStatuses = function(new_status) {
		chosenServices = [];
		
		$.each(this.availableServiceRequests, function(index, data){				
			if (data.service_selected) {			
				chosenServices.push(data);
			}				
		});

		if (chosenServices.length == 1) {
			this.changeStatus(chosenServices[0], new_status);
		}
		//pop up multiple confirmation
		else {
			this.changeMultipleStatusPopUp(chosenServices, new_status);
		}
	};
	
	this.changeMultipleStatusPopUp = function (rows, new_status) {
		tmp = this;
		this.rows_to_change = rows;
		this.new_status_to_apply = new_status;
		
		var modalInstance = $modal.open({
		  templateUrl: 'myMultipleConfirmationModalContent.html',
		  controller: 'multipleConfirmationCtrl',	
		  //this passes the main scope status to the controller one
		  resolve: {
			service_requests: function () {
			  return rows;
			},
			new_status: function () {
			  return tmp.statusOf[new_status];
			}
		  }
		});
		
		modalInstance.result.then(function () {	
			$.each(tmp.rows_to_change, function(index, data){				
				if (tmp.new_status_to_apply != data.status) {
					data.status = tmp.new_status_to_apply; 
					tmp.updateServiceRequestStatus(data);					
				}				
			});
						
		}, function () {
		  $log.info('Modal dismissed at: ' + new Date());
		});
	};
	
	this.reset_session = function() {
		this.session = {status: '1'};
	};		
	
	this.reset_session();	
	this.GetServiceData();
	this.GetProfessionals();
	this.GetWorkers();	
	this.GetServiceRequests(0, $routeParams.buildingId, $routeParams.tenantId, $routeParams.workerId, $routeParams.professionalId);	
	this.MultiTypeElements();
}]);

angular.module('sam').controller('confirmationCtrl', ['$scope', '$modalInstance','service_request', 'new_status', function($scope, $modalInstance, service_request, new_status) {

	$scope.service_request = service_request; 
	$scope.new_status = new_status;

	$scope.ok = function () {
		$modalInstance.close();
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
}]);

angular.module('sam').controller('servicePreventionModalCtrl', ['$scope', '$modalInstance', function($scope, $modalInstance) {

	$scope.ok = function (delete_status) {
		$modalInstance.close(delete_status);
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
}]);

angular.module('sam').controller('multipleConfirmationCtrl', ['$scope', '$modalInstance','service_requests', 'new_status', function($scope, $modalInstance, service_requests, new_status) {

	$scope.service_requests = service_requests; 
	$scope.new_status = new_status;

	$scope.ok = function () {
		$modalInstance.close();
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
}]);

angular.module('sam').controller('reminderCtrl', ['$scope', '$modalInstance', 'building_name', 'tenant_name', 'worker_name', 'professional_name', 'sms_content', 'service_request', 'entities', 'chosenEntities', 'workers', 'worker_id', function($scope, $modalInstance, building_name, tenant_name, worker_name, professional_name, sms_content, service_request, entities, chosenEntities, workers, worker_id) {

	$scope.building_name = building_name;
	$scope.tenant_name = tenant_name;
	$scope.worker_name = worker_name;
	$scope.professional_name = professional_name;
	$scope.sms_content = sms_content;
	$scope.service_request = service_request;
	$scope.entities = entities;
	$scope.chosenEntities = chosenEntities;
	$scope.workers = workers;
	$scope.worker_id = worker_id;

	$scope.ok = function (smsDetails) {
		$modalInstance.close(smsDetails);
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
}]);

angular.module('sam').controller('multipleReminderCtrl', ['$scope', '$modalInstance', 'service_requests', 'workers', function($scope, $modalInstance, service_requests, workers) {
	
	$scope.service_requests = service_requests;	
	$scope.workers = workers;

	$scope.ok = function (smsDetails) {
		$modalInstance.close(smsDetails);
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
}]);