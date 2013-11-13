#!/Users/burmisha/.rvm/rubies/ruby-2.0.0-p247/bin/ruby
require 'exifr'
require 'net/http'
require 'yaml'
require 'json'

file = 'db/index.html'
file = 'db/test.html'
thing = YAML.load_file(file)
gps = []

Net::HTTP.start("img-fotki.yandex.ru") do |http|
  thing['photos'].each_with_index { |file_id, index|
    path = "/get/" + file_id['url'] + "_orig.jpg"
    resp = http.get(path)
    jpeg = StringIO.new
    jpeg << resp.body
    begin
      jpeg.rewind
      latitude = EXIFR::JPEG.new(jpeg).gps.latitude.round(6)
      jpeg.rewind
      longitude = EXIFR::JPEG.new(jpeg).gps.longitude.round(6)
      thing['photos'].at(index)['gps'] = "#{latitude},#{longitude}"
      puts path + ": " +"#{latitude},#{longitude}"
      gps << {'type' => 'Feature' ,
              'geometry' => {'type'=> 'Point', 'coordinates' => ["#{latitude}", "#{longitude}"]} ,
              'properties'=> { 'title' => "Marker #{index}",
                               'description' => "#{index}",
                               'marker-color' => '#CC0033'} }
    rescue
      puts path + ": " + "\n"
    end
  }
end

File.open(file + '.gps', 'w') {|f| f.write thing.to_yaml }
File.open(file + '.json', 'w') {|f| f.write gps.to_json }
