$(function() 
{             
    var history = [];
    var currentIndex = -1;
    var eventSource = null;    
    
    $('#serverMsg').height($(window).height() - 330);
    
    
    function progress(percent, $element) {
	
	var progressBarWidth = percent * $element.width() / 100;
	if (percent != 0){
	    $element.find('div').animate({ width: progressBarWidth }, 50).html(percent + "%&nbsp;");
	}
	else {
	    $element.find('div').animate({ width: progressBarWidth }, 800).html("");;
	}
    }

    
    function updateTemplates()
    {        
        $.ajax(
        {        
            type: "GET",        
            url  : "/getCustomerTemplates",
	    data: $("#mainFrm").serialize(),
            success : function(data, textStatus, jqXHR){
            
                $('#printingFormat').empty();
                
                $.each(data.templates, function(i, template){
                $('#printingFormat')
                    .append($("<option></option>")
                    .prop("value",template[1])
                    .text(template[0]));
                });            
            }
        });
        
        var choice = $('#executionType')[0].selectedIndex;          
          /*
          0 - debt analizing
	  1 - events handling
          2 - general mailing
          3 - special debts
	  4 - history
	  5 - debts percentage 
	  6 - occasional messages
	  
          */                    
	  
          if (choice == 0 || choice == 5){
              $('#reportingLabel').show( "slow" );
              $('#inArowContainer').show( "slow" );
              $('#ThresholdTagsContainer').show( "slow" );
              $('#YearTagsContainer').show( "slow" );
	      $('#monthsTagsContainer').show( "slow" );
	      $('#ApprtmentChoice').hide( "slow" );
	      $('#EventContainer').hide( "slow" );
	      $('#MailSubjectContainer').hide( "slow" );
	      $('#OccasionalMsgContainer').hide( "slow" );      
	      
	      if (choice ==0) {
		$('#li_format').show( "slow" );
	      }
	      if (choice ==5) {
		$('#li_format').hide( "slow" );
	      }	      
          }
	  else if (choice == 1){
              $('#reportingLabel').hide( "slow" );
              $('#ThresholdTagsContainer').hide( "slow" );
              $('#YearTagsContainer').hide( "slow" );
	      $('#monthsTagsContainer').hide( "slow" );
	      $('#ApprtmentChoice').hide( "slow" );
	      $('#EventContainer').show( "slow" );
	      $('#MailSubjectContainer').hide( "slow" );
	      $('#OccasionalMsgContainer').hide( "slow" );      
	      $('#li_format').show( "slow" );	      
          }
	  
	  else if (choice == 6){
              $('#reportingLabel').hide( "slow" );
              $('#ThresholdTagsContainer').hide( "slow" );
              $('#YearTagsContainer').hide( "slow" );
	      $('#monthsTagsContainer').hide( "slow" );
	      $('#ApprtmentChoice').hide( "slow" );	    
	      $('#EventContainer').hide( "slow" );	      
	      $('#li_format').show( "slow" );      
	      $('#MailSubjectContainer').show( "slow" );
	      $('#OccasionalMsgContainer').show( "slow" );      
          }
	  
          else if (choice == 2){
              $('#reportingLabel').hide( "slow" );
              $('#ThresholdTagsContainer').hide( "slow" );
              $('#YearTagsContainer').hide( "slow" );
	      $('#monthsTagsContainer').hide( "slow" );
	      $('#ApprtmentChoice').hide( "slow" );
	      $('#EventContainer').hide( "slow" );
	      $('#MailSubjectContainer').hide( "slow" );
	      $('#OccasionalMsgContainer').hide( "slow" );      
	      $('#li_format').show( "slow" );	      
          }	  
          else if (choice == 3){       
              $('#reportingLabel').show( "slow" );
              $('#inArowContainer').hide( "slow" );              
              $('#ThresholdTagsContainer').show( "slow" );
	      $('#monthsTagsContainer').hide( "slow" );
              $('#YearTagsContainer').show( "slow" );
	      $('#ApprtmentChoice').hide( "slow" );
	      $('#EventContainer').hide( "slow" );
	      $('#MailSubjectContainer').hide( "slow" );
	      $('#OccasionalMsgContainer').hide( "slow" );      
	      $('#li_format').show( "slow" );	      
          }
	  else if (choice == 4){       
              $('#reportingLabel').hide( "slow" );
              $('#ThresholdTagsContainer').hide( "slow" );
              $('#YearTagsContainer').hide( "slow" );
	      $('#monthsTagsContainer').hide( "slow" );
	      $('#li_format').hide( "slow" );	      
	      $('#EventContainer').hide( "slow" );
	      $('#MailSubjectContainer').hide( "slow" );
	      $('#OccasionalMsgContainer').hide( "slow" );      
	      $('#ApprtmentChoice').show( "slow" );
          }
    }
    
    function welcome()
    {
        history = [];
        if (eventSource){
            eventSource.close();
        }
        
        $('#control_panel').hide();
        history = [];
        currentIndex = -1;                
        
        $.ajax(
        {        
            type: "GET",        
            url  : "/welcome",            
            success : function(data, textStatus, jqXHR){                                    
                $('#serverMsg').html(data.message);                            
                $('#labelMsg').html(data.label);                            
                $('#serverMsg').attr("msg_type", data.type);        
            }
        });
        
    }
    
    function showInfo(info)
    {    
        $('#serverMsg').attr("dir", info.direction);
        $('#serverMsg').html('<span id="printSection" dir="rtl">' + info.message + '</span>');
        
        if (info.hasOwnProperty('label') && 'null' != info.label){
            $('#labelMsg').html(info.label);
        }
                
        if (info.hasOwnProperty('progress') && null != info.progress){
	    progress(info.progress, $('#progressBar'));
        }
        
        
        
        $('#serverMsg').attr("msg_type", info.type);
	if (info.type == 'error'){
	    $('#control_panel').show('slow');
	}
    }
    
    welcome();
    updateTemplates();
    
    
    
    //when adding a tag to the ignores, make sure it is removed from the includes
    $("#ignoreTags").tagit({                
        afterTagAdded: function(event, ui) {
        
            tagAddedLabel = $(ui.tag[0]).find('.tagit-label').text();
            currentIncludes = $("#includeTags").tagit("assignedTags");
            
            if (currentIncludes.indexOf(tagAddedLabel) >= 0){            
                $('#includeTags').tagit('removeTagByLabel', tagAddedLabel);
            }            
        }
    });
    
    //when adding a tag to the includes, make sure it is removed from the ignores
    $("#includeTags").tagit({                
        afterTagAdded: function(event, ui) {  
        
            tagAddedLabel = $(ui.tag[0]).find('.tagit-label').text();
            currentIgnores = $("#ignoreTags").tagit("assignedTags");
            
            if (currentIgnores.indexOf(tagAddedLabel) >= 0){            
                $('#ignoreTags').tagit('removeTagByLabel', tagAddedLabel);
            }            
        }
    });
    
    $("#appartmentTags").tagit({                        
        placeholderText :'הקלד דירה או מספר דירות',
	allowSpaces: true
    });
    
    //$("#yearTags").tagit({                
        //tagLimit :1,
        //placeholderText :'הקלד שנה' ,
        //onTagLimitExceeded : function(event, ui) {
            //alert('לא ניתן להפיק דו"ח יותר משנה אחת');
        //}
    //});
    
    //$("#monthsTags").tagit({                
        //placeholderText : 'הקלד חודש או טווח חודשים'
    //});
    
    //$("#ThresholdTags").tagit({
	//tagLimit :1,
        //placeholderText : 'הקלד גבול תחתון לסכום חוב', 
	//onTagLimitExceeded : function(event, ui) {
            //alert('לא ניתן להפיק דו"ח על יותר מסכום אחד');
        //}
    //});
    
    $.ajax(
    {        
	type: "GET",        
	url  : "/getCache",        
	success : function(data, textStatus, jqXHR)
	{		    
	    
	    if (data.hasOwnProperty('ignores')){
		$.each(data.ignores, function(index, value){
		    $('#ignoreTags').tagit("createTag", value);
		});
	    }
	    
	    if (data.hasOwnProperty('includes')){
		$.each(data.includes, function(index, value){
		    $('#includeTags').tagit("createTag", value);
		});
	    }
	    
	    if (data.hasOwnProperty('months')){
		$('#monthsInput').val(data.months);
	    }
	    
	    //if ($('#monthsInput').val().length == 0){
		//var today = new Date();
		//var currentMonth = today.getMonth() + 1;
		//$('#monthsInput').val(sprintf("1-%d", currentMonth));		
	    //}
				
				
	    if (data.hasOwnProperty('reportOnlyIfAllInARow')){
		$('#inArow').prop('checked', data.reportOnlyIfAllInARow);                            
	    }
	    
	    if (data.hasOwnProperty('threshold')){
		$('#ThresholdInput').val(data.threshold);		
	    }
	    
	    if (data.hasOwnProperty('year')){
		$('#yearInput').val(data.year);
	    }
	    
	    if ($('#yearInput').val().length == 0){
		var today = new Date();
		var currentYear = today.getFullYear();
		$('#yearInput').val(currentYear);		
	    }
	    
	    $.ajax(
	    {        
		type: "GET",        
		url  : "/getBuildings",  
		data: $("#mainFrm").serialize(),
		success : function(data, textStatus, jqXHR)
		{                      
		    $(".buildingTags").tagit({
			availableTags: data.buildings,
			allowSpaces: true,
			placeholderText : 'התחל להקליד שם של בניין'
		    });            
		},
	       error: function(XMLHttpRequest, textStatus, errorThrown) {                                
		    console.log(XMLHttpRequest.statusText);                    
	       }
	    });
	    
	},
       error: function(XMLHttpRequest, textStatus, errorThrown) {                                
	    console.log(XMLHttpRequest.statusText);                    
       }
    });        
       
    
    $(document).on( "click", "button.support", function(e) {        
        var request = $.ajax(
        {        
            type: "POST",     
            url: "/support",
	    data: {supportMsg: $('#printSection').text()}            
        });
	
	request.done(function(msg) {
	    alert(sprintf('בקשת תמיכה נקלטה במערכת ומספרה : #%s . יום נעים.', msg.supportRequestId));
	});
 
	request.fail(function( jqXHR, textStatus ) {
	    alert('בקשת תמיכה נכשלה.');
	});
        
    });
    
    $(document).on( "click", "button.ignore", function(e) {        
        $('#ignoreTags').tagit('createTag', e.target.id);
        
    });
    
    $(document).on( "click", "#reset", function(e) {
        $('.GeneralTags').tagit("removeAll");
	$('#monthsInput').val('');
	$('#yearInput').val('');
	$('#ThresholdInput').val('');
        welcome();
    });
    
    $(document).on( "click", "#next", function(e) {        
        if (currentIndex < history.length - 1)
        {
            currentIndex += 1;
            var info = history[currentIndex];
            showInfo(info);
        }                    
    });  
    
    
    $(document).on( "click", "#check_renters", function(e) {
	rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
	    toMark = $(this).prop('class').indexOf('renter') > -1 ? true : false
	    
            $(this).find('.tenantCheckBox').prop('checked', toMark);
	    $(this).find('.smsCheckBox').prop('checked', toMark);
	    $(this).find('.mailCheckBox').prop('checked', toMark);
	    $(this).find('.letterCheckBox').prop('checked', toMark);
	    $(this).find('.billboardCheckBox').prop('checked', toMark);
        });
    });
    
    $(document).on( "click", "#check_owners", function(e) {
	rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
	    toMark = $(this).prop('class').indexOf('owner') > -1 ? true : false
	    
            $(this).find('.tenantCheckBox').prop('checked', toMark);
	    $(this).find('.smsCheckBox').prop('checked', toMark);
	    $(this).find('.mailCheckBox').prop('checked', toMark);
	    $(this).find('.letterCheckBox').prop('checked', toMark);
	    $(this).find('.billboardCheckBox').prop('checked', toMark);
        });
    });
    
    $(document).on( "click", "#check_defacto", function(e) {
	rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
	    toMark = $(this).prop('class').indexOf('defacto') > -1 ? true : false
	    
            $(this).find('.tenantCheckBox').prop('checked', toMark);
	    $(this).find('.smsCheckBox').prop('checked', toMark);
	    $(this).find('.mailCheckBox').prop('checked', toMark);
	    $(this).find('.letterCheckBox').prop('checked', toMark);
	    $(this).find('.billboardCheckBox').prop('checked', toMark);
        });
    });
    
    $(document).on( "click", "#check_all", function(e) {
	rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
	    toMark = true;
	    
            $(this).find('.tenantCheckBox').prop('checked', toMark);
	    $(this).find('.smsCheckBox').prop('checked', toMark);
	    $(this).find('.mailCheckBox').prop('checked', toMark);
	    $(this).find('.letterCheckBox').prop('checked', toMark);
	    $(this).find('.billboardCheckBox').prop('checked', toMark);	    	    
        });
    });
    
    $(document).on( "change", ".tenantCheckBox", function(e) {	
	row = $(this).parents('tr')
	row.toggleClass( "strike_thorugh" );
	row.find('.smsCheckBox').prop('checked', $(this).prop('checked'));
	row.find('.mailCheckBox').prop('checked', $(this).prop('checked'));
	row.find('.letterCheckBox').prop('checked', $(this).prop('checked'));
	row.find('.billboardCheckBox').prop('checked', $(this).prop('checked'));
    });
    
    $(document).on( "change", ".printingFormat", function(e) {	
	row = $(this).parents('tr')
	templatesPath = $(this).val().replace(/\\/g, "*");		
	
	//first disable and later enable if there is a template for this alerts and the relevant details for this tenant (mails or sms)
	row.find('.smsCheckBox').prop('disabled', true);
	row.find('.mailCheckBox').prop('disabled', true);
	row.find('.letterCheckBox').prop('disabled', true);
	
	
	$.ajax(
	{        
	    type: "GET",        
	    url  : "/getAvailableAlertsTemplates",
	    async:   false,
	    data: $.param({ 'templatesPath': templatesPath }),
	    success : function(data, textStatus, jqXHR){  		    
		alerts = data.alerts;
		if (alerts.indexOf('sms') >= 0) {
		    phones = [];
		    $.each($(row).find('.phones .phone'),function(i, phone) {
			phones.push($(phone).text());
		    });            
		    
		    if (phones.length) {
			row.find('.smsCheckBox').prop('disabled', false);
		    }
		}
		
		if (alerts.indexOf('mail') >= 0) {
		    //There is a mail template, so enable letter checkbox
		    row.find('.letterCheckBox').prop('disabled', false);
		    
		    mails = []
		    $.each($(row).find('.mails .mail'),function(i, mail) {
			mails.push($(mail).text());
		    });  
		    if (mails.length) {
			row.find('.mailCheckBox').prop('disabled', false);			
		    }
		}
		if (alerts.indexOf('letter') >= 0) {
		    row.find('.letterCheckBox').prop('disabled', false);
		}
		
	    }
	});
		
    });
    
    $(document).on( "change", "#groupTenantCheckBox", function(e) {
        rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
            $(this).find('.tenantCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    $(this).find('.smsCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    $(this).find('.mailCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    $(this).find('.letterCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    $(this).find('.billboardCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    
	    $('#groupSmsCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    $('#groupMailCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    $('#groupLetterCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    $('#groupBillboardCheckBox').prop('checked', $("#groupTenantCheckBox").prop('checked'));
	    
	    if ($("#groupTenantCheckBox").prop('checked'))
	    {
		$(this).removeClass( "strike_thorugh" );
	    }
	    else
	    {
		$(this).addClass( "strike_thorugh" );		
	    }
	    
        });
    });
    
    $(document).on( "click", "#groupSmsCheckBox", function(e) {
        rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
            $(this).find('.smsCheckBox').prop('checked', $("#groupSmsCheckBox").prop('checked'));
        });
    });
    
    $(document).on( "click", "#groupMailCheckBox", function(e) {
        rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
            $(this).find('.mailCheckBox').prop('checked', $("#groupMailCheckBox").prop('checked'));
        });
    });
    
    $(document).on( "click", "#groupLetterCheckBox", function(e) {
        rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
            $(this).find('.letterCheckBox').prop('checked', $("#groupLetterCheckBox").prop('checked'));
        });
    });

    $(document).on( "click", "#groupBillboardCheckBox", function(e) {
        rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
            $(this).find('.billboardCheckBox').prop('checked', $("#groupBillboardCheckBox").prop('checked'));
        });
    });


    $(document).on( "click", "#back", function(e) {        
        if (currentIndex > 0)
        {
            currentIndex -= 1;
            var info = history[currentIndex];
            showInfo(info);
        }
    });
    
    $(document).on( "click", "#first", function(e) {
        if (history.length)
        {
            currentIndex = 1;
            $('#back').trigger('click');
        }
        
    });  
    
    $(document).on( "click", "#last", function(e) {
        if (history.length)
        {
            currentIndex = history.length-2;
            $('#next').trigger('click');              
        }        
    });         
    
    $(document).on( "click", "#print", function(e) {
        $('#printSection').printElement();        
    });  
    
    
    
    $( document ).tooltip({      
      items: ".smsToolTip, .mailToolTip, .letterToolTip, .historyToolTip",      
      track: true,      
      content: function() {	
	
	var $element = $( this );
	var content = ""
	
	if ($element.hasClass( "historyToolTip" )){
	    $.ajax(
	    {        
		type: "GET",        
		url  : "/getFileContent",
		async:   false,
		data: $.param({ 'file': $element.attr('id') }),
		success : function(data, textStatus, jqXHR){  		    
		    content = data.content;		    
		}
	    });
	}
	
	else {
	    
	    t = {};
	    phones = [];
	    mails = [];
	    	    	    
	    row = $element.parents('tr.tenantData');        
	    
	    building = $(row).find('.building').text();
	    name = $(row).find('.name').text();
	    
	    $.each($(row).find('.phones .phone'),function(i, phone) {
		phones.push($(phone).text());
	    });            
	    
	    $.each($(row).find('.mails .mail'),function(i, mail) {
		mails.push($(mail).text());
	    });            
	    
	    appartment = $(row).find('.appartment').text();
	    year = $(row).find('.year').text();
	    months = $(row).find('.months').text();
	    payment = $(row).find('.payment').text();
	    debt = $(row).find('.debt').text();
	    previousDebt = $(row).find('.previousDebt').text();
	    totalDebt = $(row).find('.totalDebt').text();
	    description = $(row).find('.description').text();
	    comment = $(row).find('.comment').text();
	    general = $(row).find('.general').text();
	    event = $(row).find('.event').text();
	    occasional = $(row).find('.occasional').text();
	    monthsCount = $(row).find('.monthsCount').text();
	    subject = $(row).find('.subject').text();
	    printingFormat = $(row).find('.printingFormat ').val();
	    
	    //new stuff
	    updatedPayment = $(row).find('.updatedPayment').text();
	    initialDebt = $(row).find('.initialDebt').text();
	    cleaningDebt = $(row).find('.cleaningDebt').text();
	    totalSpecialDebt = $(row).find('.totalSpecialDebt').text();
	    debt2011 = $(row).find('.debt2011').text();
	    debt2012 = $(row).find('.debt2012').text();
	    debt2013 = $(row).find('.debt2013').text();
	    
	    classes = $(this).prop('class');
				
	    t['building'] = building;	
	    t['name'] = name;	
	    t['phones'] = phones;	
	    t['mails'] = mails;        	
	    t['appartment'] = appartment;	
	    t['months'] = months;	
	    t['year'] = year;
	    t['payment'] = payment;	
	    t['debt'] = debt;
	    t['previousDebt'] = previousDebt;
	    t['totalDebt'] = totalDebt;
	    t['description'] = description;
	    t['comment'] = comment;
	    t['general'] = general;
	    t['event'] = event;
	    t['occasional'] = occasional;
	    t['monthsCount'] = monthsCount;
	    t['subject'] = subject;
	    t['printFormat'] = printingFormat;
	    t['toolTipClasses'] = classes;
	    
	    //new stuff
	    t['updatedPayment'] = updatedPayment
	    t['initialDebt'] = initialDebt
	    t['cleaningDebt'] = cleaningDebt
	    t['totalSpecialDebt'] = totalSpecialDebt
	    t['debt2011'] = debt2011
	    t['debt2012'] = debt2012
	    t['debt2013'] = debt2013
	    	    
	    $.ajax(
	    {        
		type: "GET",        
		url  : "/getToolTipContent",
		async:   false,
		data: $.param({ 'tenant': JSON.stringify(t), 'executionType': $('#executionType').val() }),
		success : function(data, textStatus, jqXHR){  		    
		    content = data.content;
		}
	    });
	}
	
        return content;                                   
            
    }});
    
    $(document).on( "click", "#chooseBuildingToDebt", function()
    {
	$('#includeTags').tagit("removeAll");
	$('#ignoreTags').tagit("removeAll");
	//switch to debts mode
	$('#executionType').val(0)
        rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
	    building = $(this).find('.building').text();
	    
	    if ($(this).find('.tenantCheckBox').prop('checked')) {            
		$('#includeTags').tagit("createTag", building);
	    }
        });	
	
	$( "#dialog" ).dialog( "destroy" );
	$( "#submitBtn" ).click();
	
    });
    
    $(document).on( "click", "#approveTenants", function()
    {      
	if (eventSource){
	    eventSource.close();
	}
	  
        $('body').addClass("loading");
		
	tenantsOf = {};
	totalAlerts = 0;
        rows = $('#tenantsTable').find('tr.tenantData');
        $.each(rows,function(i, row) {
            t = {}
            phones = []
            mails = []
            
            building = $(this).find('.building').text();	    
            name = $(this).find('.name').text();
            
            $.each($(this).find('.phones .phone'),function(i, phone) {				
                phones.push($(phone).text());
            });            
            
            $.each($(this).find('.mails .mail'),function(i, mail) {						
                mails.push($(mail).text());
            });            
            
            appartment = $(this).find('.appartment').text();	    
	    year = $(this).find('.year').text();
            months = $(this).find('.months').text();	    
            payment = $(this).find('.payment').text();
	    debt = $(this).find('.debt').text();
	    previousDebt = $(this).find('.previousDebt').text();
	    totalDebt = $(this).find('.totalDebt').text();
            description = $(this).find('.description').text();
	    comment = $(this).find('.comment').text();
	    general = $(this).find('.general').text();
	    event = $(this).find('.event').text();
	    occasional = $(this).find('.occasional').text();
	    monthsCount = $(this).find('.monthsCount').text();
	    subject = $(this).find('.subject').text();
	    printingFormat = $(this).find('.printingFormat ').val();
            smsCheckBox = $(this).find('.smsCheckBox').prop('checked') && !$(this).find('.smsCheckBox').prop('disabled');
            mailCheckBox = $(this).find('.mailCheckBox').prop('checked') && !$(this).find('.mailCheckBox').prop('disabled');
            letterCheckBox = $(this).find('.letterCheckBox').prop('checked') && !$(this).find('.letterCheckBox').prop('disabled');
            billboardCheckBox = $(this).find('.billboardCheckBox').prop('checked');
	    
	    //new stuff
	    updatedPayment = $(this).find('.updatedPayment').text();
	    initialDebt = $(this).find('.initialDebt').text();
	    cleaningDebt = $(this).find('.cleaningDebt').text();
	    totalSpecialDebt = $(this).find('.totalSpecialDebt').text();
	    debt2011 = $(this).find('.debt2011').text();
	    debt2012 = $(this).find('.debt2012').text();
	    debt2013 = $(this).find('.debt2013').text();
	    
            t['building'] = building;
            t['name'] = name;
            t['phones'] = phones;
            t['mails'] = mails;
            t['appartment'] = appartment;            
            t['months'] = months;
	    t['year'] = year;
            t['payment'] = payment;
	    t['debt'] = debt;
	    t['previousDebt'] = previousDebt;	    
	    t['totalDebt'] = totalDebt;
            t['description'] = description;
	    t['comment'] = comment;
	    t['general'] = general;
	    t['event'] = event;
	    t['occasional'] = occasional;
	    t['monthsCount'] = monthsCount;
	    t['subject'] = subject;
	    t['printFormat'] = printingFormat;
	    
	    t['send_sms'] = smsCheckBox;
	    t['send_mail'] = mailCheckBox;
	    t['make_letter'] = letterCheckBox;
	    t['include_in_billboard'] = billboardCheckBox;
            
            //new stuff
	    t['updatedPayment'] = updatedPayment
	    t['initialDebt'] = initialDebt
	    t['cleaningDebt'] = cleaningDebt
	    t['totalSpecialDebt'] = totalSpecialDebt
	    t['debt2011'] = debt2011
	    t['debt2012'] = debt2012
	    t['debt2013'] = debt2013
	    
            if (smsCheckBox){
		t['phones'].forEach(function(phone) {
		    if (phone.indexOf('05') == 0){
			totalAlerts += 1;
		    }
		});		
	    }
	    
	    if (mailCheckBox){
		totalAlerts += t['mails'].length;;
	    }
	                	    
	    if (t['make_letter']){
		totalAlerts += 1;	    
	    }
	    	    
	    key = building + ',' + description;
	    
            var buildingTenants = tenantsOf[key];
	    if (!buildingTenants){
		tenantsOf[key] = [];
	    }	    
	    tenantsOf[key].push(t);                                    
        });
	
	//each alert for billboard
	totalAlerts += Object.keys(tenantsOf).length;
	
	$( "#dialog" ).dialog( "destroy" );
	$('body').removeClass("loading");
		
	uploadedFiles = []
	
	//fetch attachments
	spans = $('#files').find('span.uploaded_file');
	$.each(spans,function(i, span) {						
	      uploadedFile = span.innerHTML;
	      uploadedFiles.push(uploadedFile);	
	})
					  
	eventSource = new EventSource('/tenants?' + $.param({'tenants': JSON.stringify(tenantsOf),							    
							    'customerTemplatesDir': $('#printingFormat').val(),
							    'executionType': $('#executionType').val(),
							    'year': $('#yearInput').val(),
							    'totalAlerts': totalAlerts,
							    'uploadedFiles': uploadedFiles } ) );
	
	
	//event call backs
	eventSource.onmessage = function(e) {                          
	    var info = $.parseJSON(e.data);
	    showInfo(info);                
  
	    currentIndex = history.length
	    history.push(info);              
	}
  
	eventSource.onerror = function(e) {
	    console.log ('connection down');              
	    eventSource.close();
	}

	eventSource.addEventListener('download', function(e) {
	    var data = JSON.parse(e.data);
	    var iframe1 = document.createElement("iframe");
	    iframe1.style.display = "none";
	    document.body.appendChild(iframe1);        
	    iframe1.src = sprintf("/download/%s/%s", data.downloadFolder, data.downloadFile ) 
			    
	}, false);
	
	eventSource.addEventListener('finished', function(e) {                          
	    //$('#control_panel').show('slow');
	    ;
	}, false);
		
		      		                                              
    });
    $(document).on( "click", "#submitBtn", function()
    {      
    
	  //if (!$('#includeTags').tagit("assignedTags").length) {
	      //if (!confirm('בחרתם להפיק דו"ח עבור כל הבניינים במערכת, דבר זה עלול לקחת זמן, אנא אשרו שזוהי כוונתכם')) {
		  //return;
	      //}	      
	  //}
          //history = [];
          $('#control_panel').hide();          
          
          if (eventSource){
              eventSource.close();
          }
          
                    
          $.ajax(
          {        
              type: "GET",        
              url  : "/authorize",
              
              success : function(jsonResp, textStatus, jqXHR){				
                                                      
                  if (jsonResp.approved == 'yes')
                  {
                      var data = $("#mainFrm").serialize();					  					  					  
                      eventSource = new EventSource('/events?' + data);  
                
                      //event call backs
                      eventSource.onmessage = function(e) {                          
                          var info = $.parseJSON(e.data);
                          showInfo(info);                
                
                          currentIndex = history.length
                          history.push(info);              
                      }
                
                      eventSource.onerror = function(e) {
                          console.log ('connection down');              
                          eventSource.close();
                      }
            
                      eventSource.addEventListener('download', function(e) {			  
                          var data = JSON.parse(e.data);
                          var iframe1 = document.createElement("iframe");
                          iframe1.style.display = "none";
                          document.body.appendChild(iframe1);        
                          iframe1.src = sprintf("/download/%s/%s", data.downloadFolder, data.downloadFile ) 
                                          
                      }, false);
                      
                      eventSource.addEventListener('finished', function(e) {                          
                          $('#control_panel').show('slow');
                      }, false);
                  }
                  
                  //show error message
                  else {                      
                      var info = $.parseJSON(jsonResp.data);
                      showInfo(info);
                  }
              },
              
              error: function(XMLHttpRequest, textStatus, errorThrown){                  
                  ;              
              }
          });
          
    });    
	
    function updateBuildingsAutoComplete()
    {                
	$('body').addClass("loading");
	
        $.ajax(
        {        
            type: "GET",        
            url  : "/getBuildings",
	    data: $("#mainFrm").serialize(),
            success : function(data, textStatus, jqXHR){
		$('body').removeClass("loading");
		
		$(".buildingTags").tagit({
		    availableTags: data.buildings
	        });		                				
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) 
            {                                               
                    console.log(XMLHttpRequest.statusText);    
                    $('body').removeClass("loading");
            
            }
        });
    }
    
    $('#executionType').change(function(){
	 $('#includeTags').tagit("removeAll");
	 $('#ignoreTags').tagit("removeAll");
	 $('#appartmentTags').tagit("removeAll");
         updateTemplates();
	 updateBuildingsAutoComplete();
    });
    
    $('#yearInput').change(function(){         
	 updateBuildingsAutoComplete();
    });
  
});