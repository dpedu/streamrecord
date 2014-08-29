// Templates are loaded into this object
var ENV = {}
// the current location #hash is stored here
var HASH = ""
var HASHBEH = ""

$(document).ready(function(){
	// Add handlebar helper for each
	Handlebars.registerHelper('each', function(context, options) {
		var ret = "";
		for(var i=0, j=context.length; i<j; i++) {
			ret = ret + options.fn(context[i]);
		}
		return ret;
	});
	
	// Load templates, and when done kick it off
	initTemplates(templateNames, function(){
		$(window).trigger("hashchange");
	})
	
	// Show time
	setInterval(showTimeFunc, 1000)
	showTimeFunc()
});

function showTimeFunc(){
	var n = new Date();
	var mins = n.getMinutes()
	var secs = n.getSeconds()
	$("#time").html(n.getHours()+":"+(mins<10?"0"+mins:mins)+":"+(secs<10?"0"+secs:secs))
}

function initTemplates(names, done) {
	for(n in names) {
		source = $("#template-"+names[n]).html()
		ENV[names[n]] = Handlebars.compile(source)
		Handlebars.registerPartial(names[n], source);
	}
	done()
}

// Fetch the current hash
function getHash() {
	hash = ""+window.location.hash;
	if(hash===null || hash=="") {
		return null
	}
	return hash.substring(1)
}

// Erase the current dom
function wipe() {
	$("#container").html("")
}

// Post-render callback
function done() {
	// If the current behavior has a ui counterpart, call it
	// Search in the same way we do for behaviors
	doneUi = getBehavior(HASH, true)
	if(doneUi!=null) {
		doneUi.method()
	}
}

$(window).bind('hashchange', function(e) {
	HASH = getHash();
	if(HASH == null) {
		HASH="scheduleList" // Default view
	}
	wipe();
	
	// Find and call this hash's behavior
	behavior = getBehavior(HASH)
	if(!behavior) {
		behaviors["error"]("Unknown view!")
	} else {
		behavior.method(behavior.args)
	}
	
	// Fire page change event
	if(ui["_pageChange"]) {
		ui["_pageChange"](HASH)
	}
})
function getBehavior(HASH, findUI) {
	HASH = HASH.split("/")
	// Search for a behavior matching this hash's path
	depth = HASH.length
	// Search progressively less of the hash, trying params as arguments instead until one is found
	while(depth > 0) {
		var section = {}
		if(findUI==null) {
			section = behaviors
		} else {
			section = ui
		}
		testParts = HASH.slice(0, depth)
		for(i in testParts) {
			section = section[testParts[i]]
			if(section == null) {
				break
			}
		}
		if(typeof section == "function") {
			break
		} else if(typeof section == "object") {
			section = section["index"]
			break
		}
		depth--;
	}
	if(section == null) {
		return null
	}
	return {method:section,args:HASH.splice(depth)}
}


var behaviors = {
	error:function(message) {
		$("#container").append(ENV.error({message:message}));
	},
	view: function() {
		streamId = arguments[0][0]
		$.ajax("/api/getStream", {dataType:"json", data:{id:streamId}, success:function(getStreamData){ // TODO: add ,files=True
			$("#container").append(ENV.streams({streams:[getStreamData], single:true}));
			$("div.streams > div").each(ui.basicStreamEdit)
			done()
		}});
	},
	scheduleList:function() {
		$.ajax("/api/getStreams", {dataType:"json", success:function(data){
			for(i in data) {
				data[i].files = null;
			}
			$("#container").append(ENV.streams({streams:data}));
			$("div.streams > div").each(ui.basicStreamEdit)
			done()
		}});
	},
	files:function() {
		$.ajax("/api/getStreams", {dataType:"json", success:function(data){
			$("#container").append(ENV.downloads({streams:data}));
			//$("div.streams > div").each(ui.basicStreamEdit)
			
			// Create player
			player = $("#player").jPlayer({
				supplied:"mp3",
				swfPath:"/static/player/Jplayer.swf",
				loadedmetadata: function() {
					console.log($("#player").data("jPlayer").status.duration)
					
					$(".time-holder").html('<input class="player-slider" type="text" data-slider-step="1" data-slider-value="0"/>')
					$(".time-holder .player-slider").slider({min:0,max:parseInt($("#player").data("jPlayer").status.duration+1),tooltip:"hide"})
					
					
					
				},
				play:function() {
					
				},
				timeupdate:function(event) {
					$(".time-holder .player-slider").slider('setValue', event.jPlayer.status.currentTime);
					minutes = parseInt(event.jPlayer.status.currentTime/60)
					seconds = parseInt(event.jPlayer.status.currentTime-(minutes*60))
					$(".timeshow").html(minutes+":"+(seconds<10?"0":"")+sseconds)
					
					
				}
			})
			
			
			
			$(".playlink").on("click", function(){
				url = $(this).data("url")
				$("#player").jPlayer("setMedia", {
					title: "Test",
					mp3: url
				}).jPlayer("play")
				
				$("#playerdrop .playbtn").click(function(){
					
				})
			})
			
			done()
		}});
	},
	add: function() {
		$("#container").append(ENV.add({
											name:"New Schedule",
											url:"http://",
											time: {
												starthour:6,
												startmin: 0,
												endhour: 10,
												endmin: 15
											},
											status: 0
										}));
		$("#container").find("input[name=stream-name]").on('keyup', function(){
			value = $(this).val()
			if(value.trim() == "") {
				value="New Schedule"
			}
			$(this).closest(".panel-default").find(".panel-heading h3").html(value)
		})
		$("#container").find("form.add-schedule").on('submit', function(e) {
			e.preventDefault()
			if(validate($(this))) {
				newdata = {
					name: $(this).find("input[name=stream-name]").val(),
					url: $(this).find("input[name=stream-url]").val(),
					time: {},
					status:1
				}
				newdata.time.startHour = $(this).find("input[name=stream-starthour]").val()
				newdata.time.startMin = $(this).find("input[name=stream-startmin]").val()
				newdata.time.endHour = $(this).find("input[name=stream-endhour]").val()
				newdata.time.endMin = $(this).find("input[name=stream-endmin]").val()
				newdata.time.su = $(this).find("input[name=daysu]").is(":checked")
				newdata.time.m = $(this).find("input[name=daym]").is(":checked")
				newdata.time.t = $(this).find("input[name=dayt]").is(":checked")
				newdata.time.w = $(this).find("input[name=dayw]").is(":checked")
				newdata.time.r = $(this).find("input[name=dayr]").is(":checked")
				newdata.time.f = $(this).find("input[name=dayf]").is(":checked")
				newdata.time.sa = $(this).find("input[name=daysa]").is(":checked")
				if($(this).find("button.btn-status-ok").hasClass("active")) {
					newdata.status=0
				}
				
				$.ajax("/api/createStream", {type:"post",dataType:"json",data:{data:JSON.stringify(newdata)},
						success:function(data){
					newUserId=data["result"];
					window.location = "#view/"+newUserId
				},error:function(){
					console.log("Couldn't create user! createStream");
				}})
				
			}
			return false
		})
		done()
	},
}
