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

photoId = function(photoset_id, i) {
	return photoset_id + idSuffix(i);
}

var small = {
	"id": SMALL,
	"prefix": '<div style="background-image:url(http://img-fotki.yandex.ru/get/',
	"middle": '_orig.jpg)" id="',
	"postfix": '"></div>',
	"class": 'smallphoto',
}

var large = {
	"id": LARGE,
	"prefix": '<img src="http://img-fotki.yandex.ru/get/',
	"middle": '_orig.jpg" id="',
	"postfix": '"/>',
	"class": 'bigphoto',
}

addPhoto = function(size, photo_url, id) {
	var t
	switch (size) {
		case small.id:
			t = small
			break
		case large.id:
			t = large
			break		
	}
	return t.prefix + photo_url + t.middle + id + t.postfix
}

addDescription = function(text) {
	return '<p class="description">' + text + '</p>'
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
		t = large;
	};
	for (var i = 0; i < filenames.length; i++) {
		$(id).append(addPhoto(t.id, filenames[i], photoId(photoset.id, i)));
		$("#" + photoId(photoset.id, i)).addClass(t.class);
	};
	$(id).append(addDescription(photoset.text));

	$(id).on('click', 'img, div', function(event){
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

	$("#cv").click(function(){
		$("#content").load("cv.html");
	});

	$("#about").click(function(){
		$("#content").load("about.html");
	});

	$("#photo").click(function(){
		$("#content").empty();
		for (var j = 0; j < allPhotos.length; j++) {
			$("#content").append('<div class="photoset" id="'+ allPhotos[j].id + '"></div>');
			addPhotoset(allPhotos[j]);
		};
	});
})
