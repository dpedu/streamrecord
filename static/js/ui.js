var ui = {
	_pageChange: function(hash) {
		$("ul.navbar-nav .active").removeClass("active")
		$("a[href=#"+hash.replace(/\//g, "\\/")+"]").parent().addClass("active");
	},
	_error:function() {
		alert("x")
	},
	_modal:function(modal, content) {
		modal.find(".modal-body").html(content)
		modal.modal()
	},
	
	__streamstatus:function() {
		$(".btn-group-status button").click(function() {
			$(this).parent().find(".active").removeClass("active")
			$(this).addClass("active")
		})
	},
	add:function() {
		ui.__streamstatus()
	},
	view:function() {
		ui.__streamstatus()
	},
	scheduleList:function() {
		ui.__streamstatus()
	},
	xxx: function() {
		/*$('.dropdown-menu').on('click', function(e) {
			if($(this).hasClass('dropdown-menu-form')) {
				e.stopPropagation();
			}
		});*/
	},
	basicStreamEdit: function(streamdiv){
		$(this).find(".dropdown-menu input").each(function() {
			$(this).on('change', function(){
				streamid = $(this).closest(".panel").data("streamid");
				$.ajax("/api/changeTimeDay", {dataType:"json", data:{streamid:streamid,day:$(this).attr("name"),value:$(this).is(":checked")}, success:function(data){
					//console.log("Saved.")
				},error:function(){
					console.log("Couldn't save! changeTimeDay");
				}})
			})
		})
		$(this).find("input[name=stream-name]").each(function() {
			$(this).on('change', function() {
				streamid = $(this).closest(".panel").data("streamid");
				console.log(streamid + " to " + $(this).val());
				$.ajax("/api/changeName", {dataType:"json", data:{streamid:streamid,value:$(this).val()}, success:function(data){
					//console.log("Saved.")
				},error:function(){
					console.log("Couldn't save! changeName");
				}})
			})
		})
		$(this).find("input[name=stream-url]").each(function() {
			$(this).on('change', function() {
				streamid = $(this).closest(".panel").data("streamid");
				console.log(streamid + " to " + $(this).val());
				$.ajax("/api/changeUrl", {dataType:"json", data:{streamid:streamid,value:$(this).val()}, success:function(data){
					//console.log("Saved.")
				},error:function(){
					console.log("Couldn't save! changeName");
				}})
			})
		})
		$(this).find("input[name=stream-starthour],input[name=stream-startmin],input[name=stream-endhour],input[name=stream-endmin]").each(function() {
			$(this).on('change', function() {
				streamid = $(this).closest(".panel").data("streamid");
				thisStream = $("div.panel[data-streamid="+streamid+"]")
				$.ajax("/api/changeTime", {dataType:"json", data:{
																	streamid:streamid,
																	startHour:thisStream.find("input[name=stream-starthour]").val(),
																	startMin:thisStream.find("input[name=stream-startmin]").val(),
																	endHour:thisStream.find("input[name=stream-endhour]").val(),
																	endMin:thisStream.find("input[name=stream-endmin]").val()
																},
																success:function(data){
					//console.log("Saved.")
				},error:function(){
					console.log("Couldn't save! changeName");
				}})
			})
		})
		$(this).find(".btn-group-status button").click(function(){
			streamid = $(this).closest(".panel").data("streamid");
			var newStatus = null
			if( $(this).hasClass("btn-status-ok") ) {
				newStatus = 0
			} else if( $(this).hasClass("btn-status-stop") ) {
				newStatus = 1
			} else {
				newStatus = 1
			}
			$.ajax("/api/changeStatus", {dataType:"json", data:{id:streamid, status:newStatus},error:function(){
				console.log("Couldn't save! changeStatus");
			}})
		})
	}
}
var validators = {
	addschedule: function(form) {
		messages = []
		if(form.find("input[name=stream-name]").val().trim()=="") {
			messages.push("Name must not be blank")
		}
		if(form.find("input[name=stream-url]").val().trim()=="") {
			messages.push("URL must be a valid URL")
		}
		if(form.find("ul.dropdown-menu input:checked").length==0) {
			messages.push("No days selected")
		}
		startHour = form.find("input[name=stream-starthour]").val()
		startMin = form.find("input[name=stream-startmin]").val()
		endHour = form.find("input[name=stream-endhour]").val()
		endMin = form.find("input[name=stream-endmin]").val()
		try {
			startHour = parseInt(startHour)
			startMin = parseInt(startMin)
			endHour = parseInt(endHour)
			endMin = parseInt(endMin)
			
			
			if(startHour<0 || startHour>=24 || isNaN(startHour)) {
				messages.push("Start hour must be 0-23")
			}
			if(startMin<0 || startMin>59 || isNaN(startMin)) {
				messages.push("Start minute must be 0-59")
			}
			if(endHour<0 || endHour>=24 || isNaN(endHour)) {
				messages.push("End hour must be 0-23")
			}
			if(endMin<0 || endMin>50 || isNaN(endMin)) {
				messages.push("End minute must be 0-59")
			}
			
		} catch(err) {
			messages.push("Time values must be numeric")
		}
		
		
		
		
		if(messages.length==0) {
			return true
		}
		return messages
	}
}