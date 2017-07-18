angular.module('sam').controller('historyController', ['$scope', '$sce','$filter','$http','$log', '$location','$compile', '$routeParams', '$modal', 'User', 'ngTableParams', function($scope, $sce, $filter, $http, $log, $location, $compile, $routeParams, $modal, User, ngTableParams) {

	tmp = this;		
	//a factory which passes paramteres cross controllers
	this.user = User;
	this.historyAlerts = [];
	this.alertHebrewDescOf = {0: 'סמס', 1: 'מייל', 2: 'מכתב'};
	this.iconOf = {0: 'fa-male', 1: 'fa-suitcase', 2: 'fa-users',4: 'fa-male owner', 5: 'fa-male renter'};
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
	this.recepientData = "";	
	this.alertData = "";
	this.historyAlerts = [];
			
	this.watchAlert = -1;
	this.loading = false;
	
	this.column_alert_type = true;
	this.column_alert_building_name = true;
	this.column_alert_recepient_name = true;
	this.column_alert_updated= true;	
	this.column_alert_source = true;
	this.column_alert_destination = true;
	this.showColumnPanel = false;
	
	this.masterCheckBoxState = 1; //1- uncheck, 2-partial, 3-all		
	this.total_alerts = 0;
	this.maximum_records = 0;
	
	
	this.tableParams = new ngTableParams(
		{
			//initial sorting by a decreasing date
			sorting: {updated: "desc"}
		},
		{
			counts: [],		
			total: this.historyAlerts.length, // length of data
			getData: function($defer, params) {				
				var orderedData = tmp.orderData(tmp.historyAlerts);							

				//$defer.resolve(orderedData);
				tmp.historyAlerts = orderedData;
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
	this.zeroMatch = false;
		
	this.UpdateAlertsMetaData = function(delta) {		
		this.total_alerts += delta;
		if (!this.total_alerts) {
				this.masterCheckBoxState = 1;
			}
		else if (this.total_alerts == alerts_data.length) {
			this.masterCheckBoxState = 3;
		}
		else {
			this.masterCheckBoxState = 2;
		}						
	};
	
	this.totalAlertsFromType = function(alert_type) {
		count = 0;
		angular.forEach(this.historyAlerts, function(data, index){							
			if (data.alert_selected && data.alert_type == alert_type) {					
				count += 1;
			}
							
		});
		return count;
	};
	
	this.UpdateAlerts = function(new_alerts) {
		tmp = this;				
		tmp.total_alerts = 0;
		alerts_data = tmp.orderData(new_alerts);			
		
		//remove previous watches
		angular.forEach(tmp.historyAlerts, function(alert, index){
			alert['listener']();
		});								
		
		angular.forEach(alerts_data, function(alert, index){
			//when fetching the alerts_data, each row which is selected from the beginning will not
			if (alerts_data[index].alert_selected) {				
				tmp.UpdatealertsMetaData(1);				
			}
			
			
			//add watchers for all alerts to track changes in row selections (this is due to the fact that angular does not 
			//trigget on change methods when model is changed)				
			listener = $scope.$watch(
			//watchExpression
			function(){
				return alerts_data[index];
			}, 
			//listener
			function(nv, ov) {				
				//row check box has changed				
				if (nv.alert_selected != ov.alert_selected) {					
					//update total of alerts selected
					delta = 1;
					if (!nv.alert_selected) {
						delta *= -1;
					}		
					
					tmp.UpdateAlertsMetaData(delta);
				}
			},
			//objectEquality
			true);	
			
			//http://stackoverflow.com/questions/14957614/angular-js-clear-watch
			//store the return value from each watch. this is the function which deregister the object
			alert['listener'] = listener;
		});
				
		tmp.historyAlerts = alerts_data;		
		tmp.loading = false;		
	};
	
		
	//http://stackoverflow.com/questions/19415394/with-ng-bind-html-unsafe-removed-how-do-i-inject-html
	this.showInnerHtml = function(content, title){		
		return $sce.trustAsHtml('<b>'+title+'</b><hr/>'+content);
	};
	
	this.markAlert = function(alert_id) {
		if (alert_id === this.watchAlert) {
			this.watchAlert = -1;
		}
		else {
			this.watchAlert = alert_id;
		}
	};
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
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
		angular.forEach(this.historyAlerts, function(data, index){							
			data.alert_selected = false;			
		});
	};
	
	this.selectAll = function(){							
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.historyAlerts, function(data, index){							
			data.alert_selected = true;			
		});
	};
	
	this.selectAlertByType = function(type){
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.historyAlerts, function(data, index){				
			if(data.alert_type == type){				
				data.alert_selected = true;				
			}
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
	 			
	//call server to get all tenants' info
	this.GetAlerts = function(showmore){
		if (!showmore) {
			this.limit = 50;
		}
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp = this;
		tmp.masterCheckBoxState = 1;
		tmp.loading = true; 
		tmp.clearSelections();
		
		$http.get('/fetchAlerts', {
		params: {						
			buildingName: tmp.buildingName,
			recepientName: tmp.recepientName,			
			source: tmp.source,
			destination: tmp.destination,
			start_date: $filter('date')(tmp.user.start_dt, 'yyyy-MM-dd' ),
			end_date: $filter('date')(tmp.user.finish_dt, 'yyyy-MM-dd'),
			limit: tmp.limit
		}
		}).success(function(data) {				
			tmp.maximum_records = data.maximum_records;
			tmp.UpdateAlerts(data.alerts);			
			
		});
	};
		
	// Any function returning a promise object can be used to load values asynchronously
	this.guessAlertByColumn = function(val, column) {		
		return $http.get('/guessAlertByColumn', {
			params: {
			name: val,
			column: column
			}
		}).then(function(res) {		
			return res.data;
		});
	};
	
	this.setWatchAlert = function(alert_id){
		this.watchAlert = alert_id;
	};		
	
	this.AutoCompleteChange = function(val) {		
		if(val == "") {
			this.GetAlerts();
		}						
	};
	
	this.resendAlertsFromHistory = function(record) {
		tmp = this;

		if (confirm('אשר שליחה חוזרת') ) {
			chosenAlerts = [];
			
			if (record) {
                    alert_id = record.alert_id;
                    chosenAlerts = [alert_id];


                var modalInstance = $modal.open({
                  templateUrl: 'myResendAlertModalContent.html',
                  controller: 'resendAlertModalCtrl',
                  windowClass: 'app-modal-window',
                  resolve: {
                  record: function () {
                      return record;
                    }
                  }
                });

                modalInstance.result.then(function (record) {

                    console.log('output',record);
                    //resend this now
                    tmp.loading = true;
                    $http.post('/resendAlert',
                    $.param(
                        {'record': JSON.stringify(record)}
                    )).success(function(data) {
                        tmp.loading = false;
                        tmp.GetAlerts();
                    }).error(function(data) {
                        console.log('response alerssss: ',data);
                    });

                }, function () {
                  $log.info('Modal dismissed at: ' + new Date());
                });
            }
            else
            {
				angular.forEach(this.historyAlerts, function(data, index){
					if(data.alert_selected) {
						chosenAlerts.push(data.alert_id);
					}
				});

				tmp.loading = true;
                $http.post('/resendAlertsFromHistory',
                $.param(
                    {'alert_ids': JSON.stringify(chosenAlerts)}
                )).success(function(data) {
                    tmp.loading = false;
                    tmp.GetAlerts();
                }).error(function(data) {
                    console.log('response: ',data);
                });
			}
		}
	};		
	
	this.deleteAlertsFromHistory = function(alert_id) {
		if (confirm('אשר מחיקת רשומה') ) {
			tmp = this;
			chosenAlerts = [];
			
			if (alert_id) {				
				chosenAlerts = [alert_id];
			}
			else {				
				angular.forEach(this.historyAlerts, function(data, index){							
					if(data.alert_selected) {
						chosenAlerts.push(data.alert_id);
					}
				});
			}
							
			tmp.loading = true;
			$http.post('/deleteAlertsFromHistory', 
			$.param(
				{'alert_ids': JSON.stringify(chosenAlerts)}
			)).success(function(data) {				
				tmp.loading = false;
				tmp.GetAlerts();
			}).error(function(data) {
				console.log('response: ',data);
			});
		}
							
	};
	
	this.htmlToPdf = function(alert_id) {
		tmp = this;
		chosenAlerts = [];
		if (alert_id) {				
				chosenAlerts = [alert_id];
			}
		else {									
			angular.forEach(this.historyAlerts, function(data, index){							
				if (data.alert_selected && data.alert_type == 2) {							
					chosenAlerts.push(data.alert_id);
				}						
			});
		}				

		$http.post('/exportHtmlToPdf', 
			$.param({				
				'alert_ids': JSON.stringify(chosenAlerts)
			}
			)).success(function(data) {							
				
				var iframe1 = document.createElement("iframe");
				iframe1.style.display = "none";
				document.body.appendChild(iframe1);  				
				iframe1.src = "/" + data.file_name;
										
		});
	};
		
	//call server to get all tenants' info
	this.GetAlerts();	
	

}]);

angular.module('sam').controller('resendAlertModalCtrl', ['$scope', '$modalInstance', 'record', function($scope, $modalInstance, record) {

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

	console.log('record', record);

    $scope.alertEngDescOf = {0: "sms", 1: "mail", 2: "letter"};
    $scope.record = record;
    $scope.record.sms_data = $scope.record.alert_data;
	$scope.mail_tinyConfig = tiny2;
	$scope.letter_tinyConfig = tiny3;



    $scope.isSms =  record.alert_type == 0;
    $scope.isMail =  record.alert_type == 1;
    $scope.isLetter =  record.alert_type == 2;


	$scope.ok = function (record) {

		$modalInstance.close(record);
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
}]);

