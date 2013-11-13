#!/Users/burmisha/.rvm/rubies/ruby-2.0.0-p247/bin/ruby
require 'exifr'

folder="/Users/burmisha/Dropbox/Photo/2013/2013.08 London/DB/"

File.open('coordinates.tmp', 'w') do |output|
  Dir.glob(folder + '*.jpg') do |file|
    coordinates = ""
    begin 
      latitude = EXIFR::JPEG.new(file).gps.latitude
      longitude = EXIFR::JPEG.new(file).gps.longitude
      output.puts "#{latitude.round(6)},#{longitude.round(6)}"
    rescue
      output.puts "\n"
    end
  end
end
