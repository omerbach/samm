		
angular.module('sam').controller('paymentsController', ['$scope', '$filter','$http','$log', '$location','$compile', '$routeParams', '$modal', 'User', 'ngTableParams', function($scope, $filter, $http, $log, $location, $compile, $routeParams, $modal, User, ngTableParams) {
	
	this.availablePayments = [];	
	tmp = this;
	//a factory which passes paramteres cross controllers
	this.user = User;	
	this.maximum_records = 0;
	this.limit = 50;
	
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
		
	this.serviceData = {};	
	this.showAddForm = false;	
	this.loading = false;	
	
	this.statusOf = {1: 'נתקבל', 2:'הופקד'};	
	this.paymentTypeOf = {1: "צ'ק", 2:'מזומן', 3: 'העברה בנקאית'};	
	this.statusesWithIdle = [{status: 0, desc: 'הצג תשלומים מכל הסטטוסים'}, {status: 1,desc: 'הצג תשלומים שנתקבלו'}, {status: 2, desc: 'הצג תשלומים שהופקדו'}]
	this.filterStatus = this.statusesWithIdle[0];
	this.paymentTypesWithIdle = [{status: 0, desc: 'הצג את כל סוגי התשלומים'}, {payment_type: 1,desc: "הצג תשלומים בצ'ק"}, {payment_type: 2, desc: 'הצג תשלומים במזומן'}, {payment_type: 3, desc:'הצג תשלומים בהעברה בנקאית'}]
	this.filterPaymentType = this.paymentTypesWithIdle[0];
	
	this.column_id = false;
	this.column_status = true;
	this.column_payment_type = true;
	this.column_receipt = true;
	this.column_tenant_cheque_date = true;
	this.column_amount = true;
	this.column_tenant_bank_account = true;
	this.column_tenant_bank_branch = true;		
	this.column_tenant_cheque_identifier = true;
	this.column_payment_approval = true;
	this.column_building = true;
	this.column_tenant = true;
	this.column_apartment_number = true;
	this.column_acceptance_date = true;
	this.column_deposit_date = true;
	this.column_worker = true;
	this.column_company_bank_account = false;
	this.column_company_bank_branch = false;	
	this.column_comment = true;
	this.column_external_folder = true;		
	
	this.masterCheckBoxState = 1; //1- uncheck, 2-partial, 3-all		
	this.total_payments = 0;
	this.showColumnPanel = false;
	
	this.availableTenants = [];
	this.tableParams = new ngTableParams(
		{
			//initial sorting by a decreasing date
			sorting: {tenant_cheque_date: "desc"}               
		},
		{
			counts: [],		
			total: this.availablePayments.length, // length of data
			getData: function($defer, params) {				
				var orderedData = tmp.orderData(tmp.availablePayments);							

				//$defer.resolve(orderedData);
				tmp.availablePayments = orderedData;
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
	
	this.addNewPayment = function(){		
		tmp = this;		
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 				
		
		//convert fields which have data in their names to yyyy-MM-dd
		angular.forEach(this.session, function(value, key){	
			if (key.search('date') >= 0 ){
				tmp.session[key] = $filter('date')(value, 'yyyy-MM-dd');
			}						
		});				
				
		$http.post('/addNewPayment', 
			$.param({
				payment_details: JSON.stringify(this.session)			
			}
			)).success(function(data) {								
				tmp.loading = false; 
				tmp.showAddForm = false;
				tmp.session = {};	
				tmp.GetPayments(data.payment_ids);				
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
			this.GetPayments();
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
	
	this.open_tenant_cheque_date = function($event) {
		$event.preventDefault();
		$event.stopPropagation();

		this.opened_tenant_cheque_date = true;
	};
	
	this.open_acceptance_date = function($event) {
		$event.preventDefault();
		$event.stopPropagation();

		this.opened_acceptance_date = true;
	};
	
	this.open_deposit_date = function($event) {
		$event.preventDefault();
		$event.stopPropagation();

		this.opened_deposit_date = true;
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
		angular.forEach(this.availablePayments, function(data, index){							
			data.payment_selected = false;			
		});
	};
	
	this.selectAll = function(){							
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.availablePayments, function(data, index){							
			data.payment_selected = true;			
		});
	};
	
	this.selectPaymentByStatus = function(status){
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.availablePayments, function(data, index){			
			if(data.status == status){				
				data.payment_selected = true;				
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
	
	this.UpdatePaymentsMetaData = function(delta) {
		this.total_payments += delta;
		if (!this.total_payments) {
				this.masterCheckBoxState = 1;
			}
		else if (this.total_payments == _.keys(payments_data).length) {
			this.masterCheckBoxState = 3;
		}
		else {
			this.masterCheckBoxState = 2;
		}						
	};		
	
	this.test = function() {
		;
	};
	this.UpdatePaymentRequests = function(new_payments) {		
		tmp = this;				
		tmp.total_payments = 0;
		payments_data = tmp.orderData(new_payments);		
		
		//remove previous watches
		angular.forEach(tmp.availablePayments, function(payment, index){
			payment['listener']();
		});								
		
		angular.forEach(payments_data, function(payment, index){
			//when fetching the payments_data, each row which is selected from the beginning will not
			if (payments_data[index].payment_selected) {				
				tmp.UpdatePaymentsMetaData(1);				
			}
			
			
			//add watchers for all payments to track changes in row selections (this is due to the fact that angular does not 
			//trigget on change methods when model is changed)				
			listener = $scope.$watch(
			//watchExpression
			function(){
				return payments_data[index];
			}, 
			//listener
			function(nv, ov) {				
				//row check box has changed
				if (nv.payment_selected != ov.payment_selected) {					
					//update total of payments selected
					delta = 1;
					if (!nv.payment_selected) {
						delta *= -1;
					}		
					
					tmp.UpdatePaymentsMetaData(delta);
				}
			},
			//objectEquality
			true);	
			
			//http://stackoverflow.com/questions/14957614/angular-js-clear-watch
			//store the return value from each watch. this is the function which deregister the object
			payment['listener'] = listener;
		});
		
		tmp.availablePayments = payments_data;			
		tmp.loading = false;		
	}

	
	//call server to get all payment Requests' info
	this.GetPayments = function(payment_ids){		
			
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp = this;		
		
		tmp.masterCheckBoxState = 1;		
		tmp.loading = true; 
		tmp.clearSelections();
		
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchPayments', {
		params: {
			updated_payment_ids: JSON.stringify(payment_ids),
			status: tmp.filterStatus.status,			
			building_id: tmp.buildingData.id,
			payment_approval: tmp.approvalData,
			tenant_id: tmp.tenantData.id,			
			start_date: $filter('date')(tmp.user.start_dt, 'yyyy-MM-dd' ),
			end_date: $filter('date')(tmp.user.finish_dt, 'yyyy-MM-dd'),
			limit: tmp.limit
		}
		}).success(function(data) {			
			tmp.maximum_records = data.maximum_records;	
			tmp.UpdatePaymentRequests(_.values(data.payment_requests));				
			
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
						
			if (edit == true) {				
				tmp.showAddForm = true;
			}
			else {
				tmp.showAddForm = false;
			}
			
		});
				
		
	};
	
	this.editPayment = function(payment_details) {		
		this.showAddForm = true;	
		this.session = payment_details;	
		
		this.session.status = String(this.session.status);				
		this.session.payment_type = String(this.session.payment_type);
		
		this.UpdateBuildingTenants();							
		
		this.session.edit = true;		
	};
	
	this.copyPayment = function(payment_details) {	
		tmp = this;
		tmp.loading = false; 
		$http.post('/copyPayment', 
			$.param({
				payment_details: JSON.stringify(payment_details)		
			}
			)).success(function(data) {				
				tmp.loading = false; 				
				tmp.GetPayments(data.payment_ids);				
		});
	};
	
	this.deletePayments = function(payment_id) {
		if (this.checkDeletionPassword()) {
			tmp = this;
			chosenPayments = [];
			
			if (payment_id) {				
				chosenPayments = [payment_id];
			}
			else {				
				$.each(this.availablePayments, function(index, data){				
					if (data.payment_selected) {			
						chosenPayments.push(data.payment_id);
					}				
				});
			}
							
			tmp.loading = true;
			$http.post('/deletePayments', 
			$.param(
				{'payment_ids': JSON.stringify(chosenPayments)}
			)).success(function(data) {				
				tmp.loading = false;
				tmp.GetPayments();
			}).error(function(data) {
				console.log('response: ',data);
			});
		}
		else {
			alert('סיסמא לא חוקית');
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
	this.guessBankAccount = function(val) {			
		return $http.get('/guessBankAccount', {
			params: {
			name: val
			}
		}).then(function(res) {				
			return res.data;
		});
	};
	
	// Any function returning a promise object can be used to load values asynchronously
	this.guessPaymentApproval = function(val) {			
		return $http.get('/guessPaymentApproval', {
			params: {
			name: val
			}
		}).then(function(res) {			
			return res.data;
		});
	};
	
	
	this.changeStatus = function(row, new_status) {
		//if same status is chosen, ignore
		if (new_status == row.status) {
			return;
		}
		
		//do not allow changing back from deposit to received status
		if (new_status == 1) {			
			return;
		}
		
		this.changeStatusPopUp(row, new_status);	
		
		/* row.status = new_status;
		this.session = row;
		this.session.edit = true;		
		
		
		if (new_status == 2) {
			this.session.deposit_date = new Date();
		}		
		
		this.addNewPayment();		 */
	};
	
	this.changeStatusPopUp = function (row, new_status) {
		tmp = this;		
		
		//if same status is chosen, ignore
		if (new_status == row.status) {
			return;
		}
		
		if (!row.deposit_date) {
			row.deposit_date = new Date();
		}
		var modalInstance = $modal.open({
		  templateUrl: 'myPaymentConfirmationModalContent.html',
		  controller: 'paymentConfirmationCtrl',	
		  //this passes the main scope status to the controller one
		  resolve: {
			payment_details: function () {
			  return row;
			},
			new_status: function () {
			  return tmp.statusOf[new_status];
			}
		  }
		});
		
		modalInstance.result.then(function (paymentDetails) {			
			row.payment_approval = paymentDetails.payment_approval;			  
			row.deposit_date = paymentDetails.deposit_date;
			row.status = new_status;
			tmp.session = row;
			tmp.session.edit = true;		
						
			tmp.addNewPayment();		
		}, function () {
		  $log.info('Modal dismissed at: ' + new Date());
		});
	};
	
	this.changePaymentType = function() {
		
		//on edit mode, do not change status / deposit date
		if (this.session.edit) {
			return;
		}
		
		if (this.session.payment_type == 3) {			
			this.session.deposit_date = new Date();
			this.session.tenant_cheque_date = new Date();			
		}
		else if (this.session.payment_type == 2) {			
			this.session.tenant_cheque_date = new Date();			
		}
	};
				
	this.reset_session = function() {
		this.session = {status: '1', payment_type: '1', edit: false};		
		//acceptance_date defaults for today		
		this.session.acceptance_date = new Date();
	};	
		
	this.toStr = function(val) {
		if (_.isUndefined(val) || _.isNull(val)) {
			return "";
		}		
		return val.toString();
	};
	
	this.partialyData = function() {
		tmp = this;
		
		basicFieldExists = tmp.toStr(tmp.session.tenant_id).length > 0 && tmp.toStr(tmp.session.tenant_cheque_date).length > 0 && tmp.toStr(tmp.session.building_id).length > 0 && tmp.toStr(tmp.session.acceptance_date).length > 0 && tmp.toStr(tmp.session.amount).length > 0 && tmp.toStr(tmp.session.worker_id).length > 0 && tmp.toStr(tmp.session.receipt).length > 0;
		chequeFieldExists = tmp.toStr(tmp.session.tenant_cheque_identifier).length > 0 && tmp.toStr(tmp.session.tenant_cheque_date).length > 0 && tmp.toStr(tmp.session.tenant_bank_account).length > 0 && tmp.toStr(tmp.session.tenant_bank_branch).length > 0;				
		transferFieldExists = tmp.toStr(tmp.session.payment_approval).length > 0 && tmp.toStr(tmp.session.tenant_cheque_date).length > 0 && tmp.toStr(tmp.session.tenant_bank_account).length > 0 && tmp.toStr(tmp.session.tenant_bank_branch).length > 0;
		
		if (basicFieldExists) {
			if(tmp.session.payment_type == '2') {
				return false;
			}
			if(tmp.session.payment_type == '1' && chequeFieldExists) {
				return false;
			}
			
			if(tmp.session.payment_type == '3' && transferFieldExists) {
				return false;
			}
		} 
		return true;		
	};
	
	this.checkDeletionPassword = function(){
		var user_input = prompt("הכנס סיסמת מחיקה");
		if (user_input == 'admin') {
			return true;			
		}
		else {
			return false;
		}
	};
	
	this.reset_session();	
	this.GetServiceData();	
	this.GetWorkers();	
	this.GetPayments();
}]);

angular.module('sam').controller('paymentConfirmationCtrl', ['$scope', '$modalInstance','payment_details', 'new_status', function($scope, $modalInstance, payment_details, new_status) {

	$scope.payment_details = payment_details; 
	$scope.new_status = new_status;
	$scope.open_deposit_date = function($event) {		
		$event.preventDefault();
		$event.stopPropagation();
		
		$scope.opened_deposit_date = true;
	};

	$scope.ok = function (paymentDetails) {
		$modalInstance.close(paymentDetails);
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
}]);