findSet = function(hid) {
	for (var j = 0; j < allPhotos.length; j++) {
		if (hid.localeCompare(allPhotos[j].id) == 0){
			return j;
		}
	};
	alert("none for " + hid);
};

idSuffix = function(i) {
	return "_" + ('000'+i).slice(-3);
}

var small = {
	"id": SMALL,
	"prefix": '<div style="background-image:url(',
	"middle": ')" id="',
	"postfix": '"></div>',
	"class": 'smallphoto',
	"type": 'div'
}

var large = {
	"id": LARGE,
	"prefix": '<img src="',
	"middle": '" id="',
	"postfix": '"/>',
	"class": 'bigphoto',
	"type": 'img'
}

addPhotoset = function(photoset) {
	var id = "div#" + photoset.id;
	$(id).append('<h2>' + photoset.title + '</h2>');
	var filenames, t;
	if (photoset.size == SMALL) {
		filenames = photoset.filenames_small;
		t = small;
	} else {
		filenames = photoset.filenames;
		t = large
	};
	for (var i = 0; i < filenames.length; i++) {
		var newdiv = t.prefix + filenames[i] + t.middle + photoset.id + idSuffix(i) + t.postfix;
		$(id).append(newdiv);
	};
	$(id + " " + t.type).addClass(t.class);
	$(id).append('<p class="description">' + photoset.text + '</p>');

	$(id).on('click', t.type, function(event){
		var id = $(this).attr("id");
		var photoset = allPhotos[findSet((id).slice(0,-4))];
		$("#" + photoset.id).empty();
		photoset.size = 1 - photoset.size;
		addPhotoset(photoset); 
		$("html, body").animate({scrollTop: $("#" + id).position().top}, 800);
		event.stopImmediatePropagation()
	});
}

$(function(){
	$("#links").click(function(){
		$("#content").load("links.html");
	});

	$("#bio").click(function(){
		$("#content").load("bio.html");
	});

	$("#main").click(function(){
		$("#content").load("main.html");
	});

	$("#photo").click(function(){
		$("#content").empty();
		for (var j = 0; j < allPhotos.length; j++) {
			$("#content").append('<div class="photoset" id="'+ allPhotos[j].id + '"></div>');
			addPhotoset(allPhotos[j]);
		};
	});
})
