angular.module('sam').controller('tenantsController', ['$scope', '$filter','$http','$log', '$location','$compile', '$routeParams', '$modal', 'User', 'ngTableParams', function($scope, $filter, $http, $log, $location, $compile, $routeParams, $modal, User, ngTableParams) {
	
	//call server to get all debt types
	this.GetDebtTypes = function(){		

		tmp = this;	

		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchDebtTypes', {		
		}).success(function(data) {			
			tmp.user.debt_types = data.debt_types;
			tmp.user.debt_type = tmp.user.debt_types[0];	
			tmp.loading = false;						
		});
	};
	
	tmp = this;
	tiny1 = 	
	{
		selector:'.tiny_sms',
		content_css : "web/css/tinyMce.css",
		height : 300,		
		plugins: ["advlist autolink lists link charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime paste directionality"], 
		toolbar: "undo redo | styleselect | bold italic | link | alignleft aligncenter alignright | ltr rtl"
	};
	
	tiny2 = 	
	{
		selector:'.tiny_mail',
		content_css : "web/css/tinyMce.css",
		height : 300,		
		plugins: ["advlist autolink lists link charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime paste directionality"], 
		toolbar: "undo redo | styleselect | bold italic | link | alignleft aligncenter alignright | ltr rtl"
	};
	
	tiny3 = 	
	{
		selector:'.tiny_letter',
		content_css : "web/css/tinyMce.css",
		height : 300,		
		plugins: ["advlist autolink lists link charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime paste directionality"], 
		toolbar: "undo redo | styleselect | bold italic | link | alignleft aligncenter alignright | ltr rtl"
	};
	
	this.sms_tinyConfig = tiny1;
	this.mail_tinyConfig = tiny2;
	this.letter_tinyConfig = tiny3;
		
	//a factory which passes paramteres cross controllers
	this.user = User;
	
	if (_.isUndefined(this.user.debt_types)) {
		this.GetDebtTypes();
		//this.user.debt_type = '1';
	}
	
	if (_.isUndefined(this.user.start_dt)) {
		//start at the first day of the year at midnight and 1 minute and 16 seconds
		this.user.start_dt = new Date(new Date().getFullYear() - 1, 0, 1, 16);		
	}
	
	if (_.isUndefined(this.user.finish_dt)) {
		//end date defaults for today
		this.user.finish_dt = new Date();	
	}		
	
	this.column_building_name = true;
	this.column_apartment = true;
	this.column_tenant_name = true;
	this.column_phones = true;
	this.column_mails = true;
	this.column_debt_description = true;
	this.column_payment = true;
	this.column_months = true;
	this.column_debt = true;	
	this.showColumnPanel = false;
	
	this.showSendSummery = false;
	this.highlightTemplate = false;
	this.showDemoPanel = false;	
	this.showTemplatesSaveButton = false;
	this.templates = [];
	this.templateData = "";
	this.buildingDescription = "";
	this.filterOptions = {
		filterText: ''
	};	
	this.selectedRow = {};	
	this.allBuildings = {};	
	this.selectedBuildings = [];
	
	this.masterCheckBoxState = 1; //1- uncheck, 2-partial, 3-all	
	this.total_tenants = 0;
	this.total_tenants_debt = 0;
	this.show_only_debts = false;
	this.show_only_consecutive_debts = false;

	this.loading = false;
	this.elements = [];		
		
	this.tableParams = new ngTableParams(
		{	
			//initial sorting by a decreasing date
			sorting: {name: "asc", index: "asc"}
		},
		{
			counts: [],		
			total: this.elements.length,
			getData: function($defer, params) {				
				var orderedData = tmp.orderData(tmp.elements);							
				
				tmp.elements = orderedData;
			}
		}
	);
	
	this.orderData = function(data) {				
		params = this.tableParams;				
		
		var orderedData = params.sorting() ?
									$filter('orderBy')(data, params.orderBy()) :
									data;
			
		return orderedData;
		
	};
	
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	};	
	this.alerts = 	{'sms': {'icon': 'fa-comment-o','hebrew': 'סמס', 'count': 0}, 
					'mail': {'icon': 'fa-envelope-o','hebrew': 'סמס', 'count': 0}, 
					'letter': {'icon': 'fa-file-word-o','hebrew': 'סמס', 'count': 0}};		
	
	this.doesDestinationExist = function (row, alert) {
		row['enable_'+alert] = true;
		
		disabled = false;
				
		if (alert == 'sms') {
			if (row.tenant_phones == ""){
				row['enable_'+alert] = false;
				disabled = true;
			}
		}
		else if (alert == 'mail') {
			if (row.tenant_mails == ""){
				row['enable_'+alert] = false;
				disabled = true;
			}
		}
		
		return disabled;				
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
		
	this.initRowAlertsStates = function(row) {
		row.alertStatusOf = {};
		for (alert in this.alerts) {
			row.alertStatusOf[alert] = "idle";
		}
	};
	
	this.getRowAlertState = function(alert, row)
	{				
		//if alertStatusOf is not defined, initialize alert status as Ideal to all alerts
		if (row.alertStatusOf == undefined) {
			this.initRowAlertsStates(row);		
		}
		
		if (row.alertStatusOf[alert] == 'idle') {			
			return this.alerts[alert].icon;
		}
		
		else if (row.alertStatusOf[alert] == 'sending') {
			return 'fa-spinner fa-spin';				
		}
		
		else if (row.alertStatusOf[alert] == 'sent_success') {
			return this.alerts[alert].icon + ' text-success';
		}
		
		else if (row.alertStatusOf[alert] == 'sent_failure') {
			return this.alerts[alert].icon + ' text-danger';
		}
	};		
	
	this.sendTemplateAlerts = function() {
	
		if (this.alerts['sms'].count + this.alerts['mail'].count + this.alerts['letter'].count > 150) {
				confirm('לא ניתן לשלוח יותר מ- 150 התראות');
				return;
		}
					
		if ((this.templateData == "" || !this.templateData.hasOwnProperty('name')) || (!this.templateData.sms_content.length && !this.templateData.mail_content.length && !this.templateData.letter_content.length)) {		
			this.showDemoPanel = true;
			this.highlightTemplate = true;
			return;
		}
		
		this.highlightTemplate = false;					
		this.open();
		
	};
	
	this.previewTamplate = function() {
		if ((this.templateData == "" || !this.templateData.hasOwnProperty('name')) || (!this.templateData.sms_content.length && !this.templateData.mail_content.length && !this.templateData.letter_content.length)) {		
			this.showDemoPanel = true;
			this.highlightTemplate = true;
			return;
		}
		
		this.openPreviewDialoge();
	};
		
	this.sendAlerts = function(worker_id) {			
		var tmp = this;						
		$.each(this.elements, function(index, data){				
			if (data.send_letter) {
				tmp.send('letter', tmp.templateData.path, data, worker_id, tmp.templateData.letter_content);
			}
			if (data.send_mail) {
				tmp.send('mail', tmp.templateData.path, data, worker_id, tmp.templateData.mail_content, tmp.templateData.mail_subject);				
			}
			if (data.send_sms) {					
				tmp.send('sms', tmp.templateData.path, data, worker_id, tmp.templateData.sms_content);				
			}			
		});				
	};		
		
	this.send = function(alert, templatePath, tenantDetails, worker_id, template_content, subject) {			
		tenantDetails.alertStatusOf[alert] = 'sending';				
		tmp = this;
		template_details = {
			'appartment': tenantDetails.apartment_number,
			'totalDebt': tenantDetails.total_debt,
			'months': tenantDetails.months,
			'building': tenantDetails.name,
			'tenant_name': tenantDetails.tenant_name,
			'payment': tenantDetails.monthly_payment,
			'description': tenantDetails.debt_description
		};
		
		angular.forEach(tmp.dynamic_fields, function(dynamic_field, index){
			template_details[dynamic_field.template_name] = tenantDetails[dynamic_field.template_name];
		});
				
		
		$http.get('/sendTemplateAlert', {
		params: {		
			path: templatePath,
			
			details: JSON.stringify(template_details),
			alert: alert,
			tenant_id: tenantDetails.tenant_id,
			worker_id: worker_id,
			tenant_type: tenantDetails.tenant_type,
			template_content: template_content,
			subject: subject,
			tenant_phones: tenantDetails.tenant_phones,
			tenant_mails: tenantDetails.tenant_mails
		}
		}).success(function(data) {					
			tenantDetails.alertStatusOf[alert] = 'sent_success';
			//remove checkbox upon a successful delivery
			tenantDetails['send_'+alert] = false;			

			totalAlerts = tmp.alerts['sms'].count + tmp.alerts['mail'].count + tmp.alerts['letter'].count;					
			if (totalAlerts-1 == 0) {					
				tmp.showSendSummery = true;				
			}
		}).
		error(function(data) {
			tenantDetails.alertStatusOf[alert] = 'sent_failure';		  
		});	
				
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
	 	
	this.UpdateTenantsMetaData = function(delta) {
		this.total_tenants += delta;
		if (!this.total_tenants) {
				this.masterCheckBoxState = 1;
			}
		else if (this.total_tenants == _.keys(tenants_data).length) {
			this.masterCheckBoxState = 3;
		}
		else {
			this.masterCheckBoxState = 2;
		}						
	};		
	
	this.InitAlertsPerTenant = function(tenant) {
		//the initial state is undefined so set it to false
		angular.forEach(_.keys(tmp.alerts), function(alert, index){
			tenant['send_'+alert] = false;
		});
		
	};
	
	this.UpdateTenants = function(new_tenants) {		
		apartmentOf = {};
		tmp = this;				
		tmp.total_tenants_debt = 0;				
		tmp.total_tenants = 0;
		tmp.alerts = 	{'sms': {'icon': 'fa-comment-o','hebrew': 'סמס', 'count': 0}, 
					'mail': {'icon': 'fa-envelope-o','hebrew': 'סמס', 'count': 0}, 
					'letter': {'icon': 'fa-file-word-o','hebrew': 'סמס', 'count': 0}};		
		tenants_data = tmp.orderData(new_tenants);			
		//initialize alert check boxes
		angular.forEach(tmp.elements, function(data, index){				
			tmp.initRowAlertsStates(data);
		});

		//remove previous watches
		angular.forEach(tmp.elements, function(tenant, index){
			tenant['listener']();
		});								
		
		angular.forEach(tenants_data, function(tenant, index){
			//when fetching the tenants_data, each row which is selected from the beginning will not
			if (tenants_data[index].tenant_selected) {				
				tmp.UpdateTenantsMetaData(1);
				tmp.InitAlertsPerTenant(tenants_data[index]);
			}
			
			
			if (tenant.total_debt > 0) {
				key = tenant.building_id+'/'+tenant.apartment_number				
				if (!(key in apartmentOf)) {
					tmp.total_tenants_debt += tenant.total_debt;
					//would have used a list but 'in' operator only implemented for objects, so value could be anything
					apartmentOf[key] = "blabla";					
				}
			}
			
			//add watchers for all tenants to track changes in row selections (this is due to the fact that angular does not 
			//trigget on change methods when model is changed)				
			listener = $scope.$watch(
			//watchExpression
			function(){
				return tenants_data[index];
			}, 
			//listener
			function(nv, ov) {				
				//row check box has changed
				if (nv.tenant_selected != ov.tenant_selected) {					
					//update total of tenants selected
					delta = 1;
					if (!nv.tenant_selected) {
						delta *= -1;
					}		
					
					tmp.UpdateTenantsMetaData(delta);
					
					//handle alerts per this row
					angular.forEach(_.keys(tmp.alerts), function(alert, index){
						//update checkbox only if it is enabled
						if (nv['enable_'+alert]){
							nv['send_'+alert] = nv.tenant_selected;							
						}							
						
					});
				}
				else {
					//alert check box has changed
					angular.forEach(_.keys(tmp.alerts), function(alert, index){
						if (nv['send_'+alert] != ov['send_'+alert] ) {
							
							if (nv['send_'+alert]) {									
								tmp.alerts[alert].count += 1;
							}
							else {										
								tmp.alerts[alert].count -= 1;								
							}	
						}
					});
				}					
			},
			//objectEquality
			true);	
			
			//http://stackoverflow.com/questions/14957614/angular-js-clear-watch
			//store the return value from each watch. this is the function which deregister the object
			tenant['listener'] = listener;
		});
		
		tmp.elements = tenants_data;		
		tmp.loading = false;		
	}
		
	 //call server to get all tenants' info
	this.GetTenants = function(){				
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp = this;
		tmp.loading = true; 
		tmp.masterCheckBoxState = 1;
		tmp.buildingDescription = "";
		tmp.showSendSummery = false;
		tmp.showDemoPanel = false;
		tmp.master_alert_column_letter = false;
		tmp.master_alert_column_mail = false;
		tmp.master_alert_column_sms = false;
		
		tmp.clearSelections();
		
		//more than one buildings in list, update its description
		if (tmp.selectedBuildings.length) {
			if (tmp.selectedBuildings.length == 1){				
				tmp.buildingDescription = tmp.allBuildings[tmp.selectedBuildings[0]].name;				
			}
			else{
				tmp.buildingDescription = tmp.selectedBuildings.length + ' ' + 'בניינים';				
			}
		}	
		//no buildings, don't call server
		else {		
			tmp.UpdateTenants([]);
			return;
		}
				
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchTenantsDebts', {
		params: {					
			updated_tenant: $routeParams.tenantId,
			show_only_debts: tmp.show_only_debts,
			show_only_consecutive_debts: tmp.show_only_consecutive_debts,
			debt_type: tmp.user.debt_type,
			minimal_debt: tmp.minimal_debt,
			element_id: JSON.stringify(tmp.selectedBuildings),
			start_date: $filter('date')(tmp.user.start_dt, 'yyyy-MM-dd' ),
			end_date: $filter('date')(tmp.user.finish_dt, 'yyyy-MM-dd')
		}
		}).success(function(data) {			
			//clear this for future calls			
			$routeParams.tenantId = 0;
			tmp.UpdateTenants(_.values(data));				
		});
	};
	
	//call server to get all builgings' info
	this.GetBuildings = function(tenantId, buildingIds){			
		tmp = this;				
		tmp.loading = true;				
		
		$http.get('/fetchBuildingsDebts', {
		params: {
			start_date: $filter('date')(tmp.user.start_dt, 'yyyy-MM-dd' ),
			end_date: $filter('date')(tmp.user.finish_dt, 'yyyy-MM-dd')						
		}
		}).success(function(data) {					
				tmp.allBuildings = data;				
				tmp.loading = false;					
				
				//when we have a tenant id from the routeParams, we need to add its building to the selectedBuildings model
				//this will trigger a get tenants call because of the ng-change of the selectedBuildings model
				if (tenantId) {						
					tmp.selectedBuildings = [tmp.serviceData.buildingIdPerTenantId[tenantId]];
				}
				//when we have some building ids  from the routeParams, we need to add them to the selectedBuildings model
				//this will trigger a get tenants call because of the ng-change of the selectedBuildings model
				else if(buildingIds) {					
					tmp.selectedBuildings = buildingIds.split(",");
				}				
				else {							
					tmp.GetTenants();
				}
		});
	};
	
	this.addAllBuildings = function() {		
		this.selectedBuildings = _.keys(this.allBuildings);
		this.GetTenants();
	};
	
	this.removeAllBuildings = function() {		
		this.selectedBuildings = [];
		this.GetTenants();
	};
		
		
	this.toggleDemoPanel = function(){
		this.showDemoPanel = !this.showDemoPanel;
	}		
	
	this.templateChanged = function(){			
		if(this.templateData == "" || _.isNull(this.templateData) || !this.templateData.hasOwnProperty('name')){
			this.highlightTemplate = true;
		}
		else {
			this.highlightTemplate = false;
		}
						
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
		
	this.fetchTemplates = function() {
		tmp = this;		
		return $http.get('/fetchTemplates_new').success(function(data) {			
			tmp.templates = data.templates;						
		});
	};		
			
	this.getTenantType = function(tenant_type) {
		if (tenant_type == 1) {
			return 'owner';
		}
		else if (tenant_type == 2) {
			return 'renter';
		}
	};
	
	this.handleMasterAlertColumn = function(alert){		
		tmp = this;
		columnAlertValue = tmp['master_alert_column_'+alert]			
		angular.forEach(this.elements, function(data, index){
			if (columnAlertValue !== data['send_'+alert]) {
				//check if checkbox is enabled
				if (data['enable_'+alert]){
					data['send_'+alert] = columnAlertValue;					
				}				
			}			
		});
	}
	
	this.clearSelections = function(){											
		tmp = this;
		angular.forEach(this.elements, function(data, index){							
			data.tenant_selected = false;			
		});
	};
	
	this.selectAll = function(){							
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.elements, function(data, index){							
			data.tenant_selected = true;			
		});
	};
	
	this.selectTenantByType = function(tenant_type){
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.elements, function(data, index){
			if(data.tenant_type == tenant_type){				
				data.tenant_selected = true;				
			}
		});
	};
	
			
  
	this.selectDefactoTenants = function(){
		this.clearSelections();
		angular.forEach(this.elements, function(data, index){				
			if(data.defacto){				
				data.tenant_selected = true;				
			}
		});
	};		
	
	//call server to update building's database
	this.UpdateDataBase = function(element_id){			
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp
		tmp = this;		
		
		//need to serialize data in angular (http://stackoverflow.com/questions/12190166/angularjs-any-way-for-http-post-to-send-request-parameters-instead-of-json)
		//as a best practice do it also when sending ajax requests via jquery
		tmp.loading = true;
		tmp.database_loading = true;
		
		// or To globally override the default transforms, override the $httpProvider.defaults.transformRequest and $httpProvider.defaults.transformResponse properties of the $httpProvider. as suggested in http://victorblog.com/2012/12/20/make-angularjs-http-service-behave-like-jquery-ajax/
		$http.post('/updateBuilding', 
			$.param(
				{'element_id': element_id}
			)).success(function(data) {
				tmp.GetBuildings();	
				tmp.loading = false;
				tmp.database_loading = false;
			}).error(function(data) {
				console.log('error: ',data);
			});
			
			
	};	
	
	this.changeStatus = function() {		
		this.open();						
	};
	
	this.openPreviewDialoge = function() {
		tmp = this;
		chosen_tenants = [];
		$.each(this.elements, function(index, data){				
			if (data.tenant_selected) {			
				chosen_tenants.push(data);
			}				
		});
		var modalInstance = $modal.open({
		  templateUrl: 'myPreviewModalContent.html',
		  controller: 'previewCtrl',	
		  size: 'lg',
		  resolve: {			
			template: function () {
			  return tmp.templateData;
			},
			tenants: function () {
			  return chosen_tenants; 
			},
			dynamic_fields: function () {
			  return tmp.dynamic_fields;
			}
		  }
		});
		
		modalInstance.result.then(function () {
		
		}, function () {
		  $log.info('Modal dismissed at: ' + new Date());
		});
	};
	
	this.open = function() {
		tmp = this;				
		var modalInstance = $modal.open({
		  templateUrl: 'myAlertsConfirmationModalContent.html',
		  controller: 'alertsConfirmationCtrl',	
		  size: 'lg',
		  resolve: {
			sms_count: function () {
			  return tmp.alerts.sms.count;
			},
			mail_count: function () {
			  return tmp.alerts.mail.count;
			},
			letter_count: function () {
			  return tmp.alerts.letter.count;
			},
			template_name: function () {
			  return tmp.templateData.name;
			},
			workers: function () {
			  return tmp.availableWorkers;
			},
			credit: function () {
			  return tmp.credit;
			}
			
		  }
		});
		
		modalInstance.result.then(function (alertDetails) {
		worker_id = alertDetails.worker_id;
		
		if (worker_id) {
			tmp.sendAlerts(worker_id);
		};
		  
		}, function () {
		  $log.info('Modal dismissed at: ' + new Date());
		});
	};
	
	this.GetServiceData = function(){			
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchServiceData', {
		}).success(function(data) {				
				tmp.serviceData = data;	
				//in building page we can enter with a couple of building id's (from building page) or with a tenant id (from main search box)
				tmp.GetBuildings($routeParams.tenantId, $routeParams.buildingIds);				
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
	
	this.CreateTenantsServiceRequest = function() {
		tmp = this;		
		$.each(this.elements, function(index, data){				
			if (data.tenant_selected) {			
				tmp.OpenServiceRequest(data);
			}				
		});							
	};
	
	this.OpenServiceRequest = function(row) {
		tmp = this;
		$location.url( '/service?tenantId='+row.tenant_id);
		
	};
	
	this.sendMail = function() {
		chosenTenants = [];		
		$.each(this.elements, function(index, data){				
			if (data.tenant_selected) {				
				chosenTenants.push('tenant-'+data.tenant_id);	
			}
		});	
				
		$location.url( '/group_mail?entities='+chosenTenants);
	};
	
	this.sendSms = function() {
		chosenTenants = [];		
		$.each(this.elements, function(index, data){				
			if (data.tenant_selected) {				
				chosenTenants.push('tenant-'+data.tenant_id);	
			}
		});	
				
		$location.url( '/group_sms?entities='+chosenTenants);
	};
	
	this.GetSmsCredit = function(){			
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchSmsCredit', {
		params: {}
		}).success(function(data) {				
			tmp.credit = data.credit;
			tmp.loading = false;				
		});
	};
	
	//call server to get all settings' info
	this.GetFields = function(updated_field){		

		tmp = this;	

		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchFields', {		
		}).success(function(data) {			
			tmp.dynamic_fields = _.values(data.fields);		
			tmp.loading = false;						
		});
	};

	

	this.getTitle = function(title) {		
		return title;
	};
	
	this.saveTamplatesChanges = function(templateData) {				
		tmp = this;	
		
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		templateData["edit"] = true;
		$http.post('/addNewTemplate', 
			$.param({
				template_details: JSON.stringify(templateData),
				sms_content: templateData.sms_content,
				mail_content: templateData.mail_content,
				mail_subject: templateData.mail_subject,
				letter_content: templateData.letter_content				
			}
			)).success(function(data) {				
				tmp.loading = false; 
				tmp.showTemplatesSaveButton = false;				
		});			
	};
		
	//this.GetDebtTypes();
	this.GetFields();
	this.GetServiceData();
	this.GetWorkers();
	this.fetchTemplates();
	this.GetSmsCredit();
		

}]);


angular.module('sam').controller('alertsConfirmationCtrl', ['$scope', '$modalInstance','sms_count', 'mail_count', 'letter_count', 'template_name', 'workers', 'credit', function($scope, $modalInstance,sms_count, mail_count, letter_count, template_name, workers, credit) {			
	$scope.sms_count = sms_count; 
	$scope.mail_count = mail_count; 
	$scope.letter_count = letter_count;
	$scope.template_name = template_name;
	$scope.workers = workers;
	$scope.credit = credit;
		
	$scope.ok = function (alertDetails) {
		$modalInstance.close(alertDetails);
	};
		
	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
			
		
}]);

angular.module('sam').controller('previewCtrl', ['$scope', '$modalInstance', '$http','$log', '$sce','template', 'tenants', 'dynamic_fields', function($scope, $modalInstance, $http, $log, $sce, template, tenants, dynamic_fields) {
	$scope.dynamic_fields = dynamic_fields;
	$scope.alerts = [{'alert_name': 'סמס', 'alert_type': 'sms'}, {'alert_name': 'מייל', 'alert_type': 'mail'}, {'alert_name': 'מכתב', 'alert_type': 'letter'}];
	$scope.template = template; 
	$scope.tenants = tenants; 
	$scope.showPreview = false;
	$scope.alert_content = {meta: "", content: ""};
		
	$scope.ok = function () {
		$modalInstance.close();
	};

	$scope.tenant_changed = function (tenant_obj, alert_obj) {		
		if (tenant_obj && alert_obj) {
			template_details = {
				'appartment': tenant_obj.apartment_number,
				'totalDebt': tenant_obj.total_debt,
				'months': tenant_obj.months,
				'building': tenant_obj.name,
				'tenant_name': tenant_obj.tenant_name,
				'payment': tenant_obj.monthly_payment,
				'description': tenant_obj.debt_description
			};
			
			angular.forEach($scope.dynamic_fields, function(dynamic_field, index){
				template_details[dynamic_field.template_name] = tenant_obj[dynamic_field.template_name];
			});
			
			$http.get('/parseAlertTemplate', {
			params: {		
				path: $scope.template.path,				
				details: JSON.stringify(template_details),
				alert: alert_obj.alert_type,
				content: $scope.template[alert_obj.alert_type+'_content'],
				mail_subject: $scope.template.mail_subject
				
			}
			}).success(function(data) {				
				$scope.alert_content = data;
			}).
			error(function(data) {
				$log.log('error!');
				$scope.alert_content = {meta: "שגיאה בתבנית", content: '<div style="background: rgb(207, 33, 33); color: white;font-size: 25px;"><p><i class="fa fa-warning"></i></p><p>נמצאה בעיה בתבנית</p><p>אנא בדקו את תוכן התבנית</p><p>ובצעו את השינויים ההכרחיים</p></div>'};
			});			
		}
		else {
			$scope.alert_content = {meta: "", content: ""};
		}
	};
	
	$scope.alert_changed = function (alert_obj, tenant_obj) {
		$scope.tenant_changed(tenant_obj, alert_obj);
	};
			
	//http://stackoverflow.com/questions/19415394/with-ng-bind-html-unsafe-removed-how-do-i-inject-html
	$scope.showInnerHtml = function(content){		
		return $sce.trustAsHtml(content);
	};
}]);