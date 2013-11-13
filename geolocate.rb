#!/Users/burmisha/.rvm/rubies/ruby-2.0.0-p247/bin/ruby
require 'exifr'
require 'net/http'
require 'yaml'

folder="/Users/burmisha/Dropbox/Photo/2013/2013.08 London/DB/"
thing = YAML.load_file('db/index.html')

File.open('coordinates.tmp', 'w') do |output|
  Net::HTTP.start("img-fotki.yandex.ru") do |http|
    #Dir.glob(folder + '*.jpg') do |file|
    for file_id in thing['photos']
      path = "/get/" + file_id['url'] + "_orig.jpg"
      resp = http.get(path)
      jpeg = StringIO.new
      jpeg << resp.body
      begin
        jpeg.rewind
        latitude = EXIFR::JPEG.new(jpeg).gps.latitude
        jpeg.rewind
        longitude = EXIFR::JPEG.new(jpeg).gps.longitude
        output.puts "#{latitude.round(6)},#{longitude.round(6)}"
        puts path + ": " +"#{latitude.round(6)},#{longitude.round(6)}"
      rescue
        output.puts "\n"
        puts path + ": " + "\n"
      end
    end
  end
end

