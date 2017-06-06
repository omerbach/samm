angular.module('sam').controller('groupMailController', ['$http', '$log', '$location', '$routeParams','$route', '$timeout', 'User', function($http, $log, $location, $routeParams, $route, $timeout, User) {
	
	tmp = this;
	this.showSendSummery = false;
	//a factory which passes paramteres cross controllers
	this.user = User;
	this.uploaded = [];	
	
	this.tinyConfig =
	{
		selector:'textarea',
		content_css : "web/css/tinyMce.css",
		height : 300,		
		plugins: ["advlist autolink lists link charmap print preview anchor image textcolor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime paste directionality"], 
		toolbar: "undo redo | styleselect | bold italic | link | alignleft aligncenter alignright | ltr rtl | forecolor backcolor",		
	};
			
	this.MultiTypeElements = function(chosen_entities){			
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchMultiTypeElements', {
		params: {		
			include_specific_buildings: true			
		}
		}).success(function(data) {	
				tmp.entities = data.entities;			
				
				if (!_.isUndefined(chosen_entities) && chosen_entities.length) {				
					tmp.chosenEntities = chosen_entities.split(',');					
				}
				tmp.loading = false;
		});
	};
	
	this.loading = false;		
    
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	};
	
	this.refresh = function(){		
		this.MultiTypeElements();
		this.clearMail();
		this.worker_id = "";
		this.showSendSummery = false;		
	};
	
	this.clearMail = function() {
		companyData = this.user.getCompanyData();
		comapnyName = companyData.comapnyName;
		comapnyWebSite = companyData.comapnyWebSite;
		comapnyLogo = companyData.comapnyLogo;
		
		this.mail_content = '<br/>' +'<br/>' +
		'בכבוד רב, ' + '<br/>' + 
		'דיצה הדר ניהול בתים משותפים בע"מ ' + '<br/>' + 
		'רחוב סוקולוב 52 א, תל-אביב.' + '<br/>' + 
		'טל –  03-5462739 שלוחה 4 | פקס – 03-5449089 | נייד -0522579871' + '<br/>' + '<br/>' +'<br/>' +
		'לנוחיותכם, ניתן לפתוח קריאות שירות ולהסדיר תשלומים דרך אתר האינטרנט של חברתנו - ditsahadar.com' + '<br/>' + '<br/>' +'<br/>' +
		'לשירותכם מיילים נוספים במשרד:' + '<br/>' + 
		'אחזקה: sherut.nihul@gmail.com   ' + '<br/>' + 
		'גבייה -          gvia1.nihul@gmail.com   ' + '<br/>' + 
		'גבייה -ראובן  :  gvia2.nihul@gmail.com    ' + '<br/>' + 
		'הנה"ח - שרי: sari.nihul@gmail.com    ' + '<br/>' +
		'משפטית- עו"ד ישראל כהן:   Israel.cohen.nihul@gmail.com' + '<br/>' +'<br/>' +
		
		'תודה מראש,' + '<br/>' + 
		
		comapnyName + '<br/>' + '<br/>' + '<a href=' + comapnyWebSite + '><img src=' + comapnyLogo +' /></a>' + '<br/><br/><br/>' + 'הופק באמצעות תוכנת' + '&nbsp;<a href="http://www.samm.co.il" target="_blank">' + '<span>SAMM</span>' + '</a>';
		this.subject = "";
		this.worker_id = "";
		this.chosenEntities = [];
		this.uploaded = [];
		this.uploaded_folder = "";
		
	};
	this.sendGroupMail = function(){
		tmp.loading = true;			
		tmp = this;
		$http.get('/sendGroupMail', {
		params: {		
			recepients: JSON.stringify(tmp.chosenEntities),
			attachments: JSON.stringify(tmp.uploaded),
			uploaded_folder: tmp.uploaded_folder,
			mail_body: tmp.mail_content,
			mail_subject: tmp.subject,
			worker_id: tmp.worker_id
		}
		}).success(function(data) {					
			tmp.loading = false;
			tmp.clearMail();
			tmp.showSendSummery = true;
			
			//http://stackoverflow.com/questions/25815160/getting-apply-is-already-in-progress-error-even-though-i-dont-explicitly-cal
			//push align right button
			$timeout(function() {
				$(".mce-i-rtl").click();
			});
		}).
		error(function(data) {
			
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
	
	this.upload = function(){
	  var data = new FormData(document.getElementById ("myForm")); // form name	
	  console.log('ffffff ', data);
	  //add uploaded folder to the form names
	  data.append('uploaded_folder', this.uploaded_folder);	  
	  $http.post('/upload', data, {                              // change with your endpoint
		transformRequest: angular.identity,
		headers: {'Content-Type': undefined}
	  })
		.success(function(result){			
			tmp.uploaded_folder = result.folder;
			angular.forEach(result.files, function(f, index){
				tmp.uploaded.push(f);
			});	
		});
	};
	
	this.removeUploadedFileFromList = function(index) {
		this.uploaded.splice(index, 1);
	};
		
	this.clearMail();
	this.GetWorkers();		
	this.MultiTypeElements($routeParams.entities);
	
		
}]);