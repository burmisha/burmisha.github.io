#!/Users/burmisha/.rvm/rubies/ruby-2.0.0-p247/bin/ruby
require 'exifr'
require 'net/http'
require 'yaml'

file = 'db/index.html'
thing = YAML.load_file(file)

Net::HTTP.start("img-fotki.yandex.ru") do |http|
  thing['photos'].each_with_index { |file_id, index|
    path = "/get/" + file_id['url'] + "_orig.jpg"
    resp = http.get(path)
    jpeg = StringIO.new
    jpeg << resp.body
    begin
      jpeg.rewind
      latitude = EXIFR::JPEG.new(jpeg).gps.latitude
      jpeg.rewind
      longitude = EXIFR::JPEG.new(jpeg).gps.longitude
      thing['photos'].at(index)['gps'] = "#{latitude.round(6)},#{longitude.round(6)}"
      puts path + ": " +"#{latitude.round(6)},#{longitude.round(6)}"
    rescue
      puts path + ": " + "\n"
    end
  }
end

File.open(file + '.gps', 'w') {|f| f.write thing.to_yaml }
