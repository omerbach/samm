(function(){	
	var app = angular.module('sam', ['ngRoute', 'ngGrid', 'ui.bootstrap', 'ui', 'ngTable', 'ui.tinymce', 'xeditable', 'checklist-model']);
	
	//http://stackoverflow.com/questions/17470790/how-to-use-a-keypress-event-in-angularjs
	app.directive('obEnter', function () {
		return function (scope, element, attrs) {
			element.bind("keydown keypress", function (event) {
				if(event.which === 13) {
					scope.$apply(function (){
						scope.$eval(attrs.obEnter);
					});

					event.preventDefault();
				}
			});
		};
	});
	
	//http://stackoverflow.com/questions/17470790/how-to-use-a-keypress-event-in-angularjs
	/* app.directive('myProgress', function () {
		return function(scope, element, attrs) {
		  scope.$watch(attrs.myProgress, function(val) {
			   element.html('<div class="bar" style="width: ' + val + '%"></div>');
		  });
		}
	}); */
	
	//http://tarruda.github.io/bootstrap-datetimepicker/ 
	app.directive('datetimez', function() {
    return {
        restrict: 'A',
        require : 'ngModel',
		//omer's fix
		priority: 10000, 
        link: function(scope, element, attrs, ngModelCtrl) {
          element.datetimepicker({            
            language: 'en',
			pick12HourFormat: false
			
          }).on('changeDate', function(e) {	
			console.log(e);
            ngModelCtrl.$setViewValue(e.date);
            scope.$apply();
          });
		  
		  scope.$watch(attrs.ngModel, function(newVal){
            var picker = $(element).data('datetimepicker');
			console.log(newVal, new Date(newVal));
            picker.setLocalDate(new Date(newVal));
          });
		  
		  
        }
    };
});
	
	app.factory("User",function($http, $log){
		//http://stackoverflow.com/questions/27386092/how-to-store-data-from-http-service-in-angular-factory?rq=1
		var data;
		var hide_status = false;
		$http.get('/getCompanyInfo').success(function (d) {
			data = d;			
		});		
		
        return {
			getCompanyData: function() {
				return data;
			},
			setNavBarHidden: function(status) {				
				hide_status = status;
			},
			getNavBarHidden: function() {				
				return hide_status;
			},
			getCompanyData: function() {
				return data;
			},
			exportHtmlTableToPdf: function(html_table_id, pdf_title) {
				toExport = [];				
				//need to maintain the orders of the headers in the table as this is important to the user's report
				headers = [];
				firstRow = true;
				
				$( "#"+ html_table_id + " tbody tr.ng-scope" ).each(function( i) {
				if ($(this).find('.checkBoxAlerts').prop('checked')) {
					row = {};			
					if (headers.length) {
						firstRow = false;
					};
					$(this).find( "td[sortable]:not(.ng-hide)" ).each(function( j) {				
						row[$(this).attr('data-title')] =  $(this).text();
						if (firstRow) {
							headers.push($(this).attr('data-title'));
						}
					});
					toExport.push(row);
				}
				});						
				
				$http.post('/exportHtmlTableToPdf', 
					$.param({
						records: JSON.stringify(toExport),						
						headers: JSON.stringify(headers),
						title: pdf_title
					}
					)).success(function(data) {							
						
						var iframe1 = document.createElement("iframe");
						iframe1.style.display = "none";
						document.body.appendChild(iframe1);  				
						iframe1.src = "/" + data.file_name;
												
				});				
			}
		
		};
	});
	app.directive('autoFocus', function($timeout) {
		return {
			restrict: 'AC',
			link: function(_scope, _element) {
				$timeout(function(){
					_element[0].focus();
				}, 0);
			}
		};
	});

	// configure our routes
	app.config(function($routeProvider) {
		$routeProvider
			
			// route for the main page which will direct to the buildings page
			.when('/', {
				templateUrl : 'web/pages/dashboard.html',
				controller  : 'dashboardController',
				controllerAs : 'dashboard'
			})
			
			// route for the main page which will direct to the buildings page
			.when('/buildings', {
				templateUrl : 'web/pages/buildings.html',
				controller  : 'mainController',
				controllerAs : 'buildings'
			})						
						
			.when('/tenants', {
				templateUrl : 'web/pages/tenants.html',
				controller  : 'tenantsController',
				controllerAs : 'tenants'
			})
			
			// route for the tenants page
			.when('/history', {
				templateUrl : 'web/pages/history.html',
				controller  : 'historyController',
				controllerAs : 'history'
			})
						
			.when('/payments', {
				templateUrl : 'web/pages/payments.html',
				controller  : 'paymentsController',
				controllerAs : 'payments'
			})
			
			// route for the tenants page
			.when('/group_mail', {
				templateUrl : 'web/pages/group_mail.html',
				controller  : 'groupMailController',
				controllerAs : 'groupMail'
			})
			
			// route for the tenants page
			.when('/group_sms', {
				templateUrl : 'web/pages/group_sms.html',
				controller  : 'groupSmsController',
				controllerAs : 'groupSms'
			})
			
			// route for the tenants page
			.when('/professionals', {
				templateUrl : 'web/pages/professionals.html',
				controller  : 'professionalsController',
				controllerAs : 'professionals'
			})					
						
			.when('/service', {
				templateUrl : 'web/pages/service.html',
				controller  : 'serviceController',
				controllerAs : 'service'
			})
						
			.when('/workers', {
				templateUrl : 'web/pages/workers.html',
				controller  : 'workersController',
				controllerAs : 'workers'
			})			
			
			.when('/settings', {
				templateUrl : 'web/pages/settings.html',
				controller  : 'settingsController',
				controllerAs : 'settings'
			})
			
			.when('/templates', {
				templateUrl : 'web/pages/templates.html',
				controller  : 'htmlTemplatesController',
				controllerAs : 'htmlTemplates'
			})
									
			;
			
	});	

	app.controller('TypeaheadSearchCtrl', function($scope, $http, $log, $location) {		
		$scope.multiElement = "";
		$scope.guessMultiElement = function(val) {		
			return $http.get('/guessMultiElement', {
				params: {
				name: val
				}
			}).then(function(res) {		
				return res.data;
			});
		};
		
		$scope.ShowElementPage = function() {			
			if ($scope.multiElement.type == "tenant")
			{				
				$location.url( '/tenants?tenantId='+$scope.multiElement.id);
			}
			
			else if ($scope.multiElement.type == "building")
			{								
				$location.url( '/buildings?buildingId='+$scope.multiElement.id);
			}
			
			else if ($scope.multiElement.type == "professional")
			{
				$location.url( '/professionals?professionalId='+$scope.multiElement.id);				
			}
			
			else if ($scope.multiElement.type == "worker")
			{
				$location.url( '/workers?workerId='+$scope.multiElement.id);				
			}
						
		}
	});
	
	app.controller('SideMenuCtrl', function($scope, $http, $log, $location) {		
		
		$scope.isRoot = function(path) {
			
			if ( $location.path() == '/' && path =='/') {
				return "active";
			}			
		};
		
		$scope.isActive = function(path) {
						
			if ($location.path().substr(0, path.length) == path) {
				return "active";
			}			
		};
	});
		
	//http://stackoverflow.com/questions/16023451/binding-variables-from-service-factory-to-controllers
	app.controller('NavBarCtrl', function($scope, $http, $log, User) {	
		$scope.hide = function() {			
			return User.getNavBarHidden();			
		}					
	});
	
	app.controller('AppController', function($scope) {
  availableTags = [
    {text: 'Apple', id: 1},
    {text: 'Apricot', id: 2},
    {text: 'Avocado', id: 3},
  ];
  $scope.select2Options = {
    tags: availableTags,
    multiple: true, 
    minimumInputLength: 1,
    formatResult: function (item) {
        return item.text;
    },
    formatSelection: function (item) {
        return item.text;
    },
  }

});
	app.controller('aboutController', function() {
		this.message = 'Look! I am an about page.';
	});

	app.controller('contactController', function() {
		this.message = 'Contact us! JK. This is just a demo.';
	});
		
		
})();