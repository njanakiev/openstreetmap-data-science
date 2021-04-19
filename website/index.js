// control that shows state info on hover
var info = L.control();
var legend = L.control({position: 'bottomright'});
var amenity_control, logistic_control;
var logistic_baseLayers = {};
var amenity_baseLayers = {};
var selected_type = 'amenity'
var data;
var colors = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', 
              '#FC4E2A', '#E31A1C', '#BD0026'];

info.onAdd = function (map) {
  this._div = L.DomUtil.create('div', 'info');
  this.update();
  return this._div;
};

info.update = function (props, key) {
  title = selected_type == 'amenity' ?'Amenity per Capita' : 'Logistic Regression';
  this._div.innerHTML = '<h4>' + title + '</h4>' +  
    (props ? '<b>' + props.name + ', ' + props.country + '<br>' + 
    (selected_type == 'amenity' ? parseFloat(props[key]).toFixed(5) + ' ' + key + ' per Capita.' : parseFloat(props[key]).toFixed(2) + ' %')
    : 'Hover over a region');
};

legend.onAdd = function (map) {
  this._div = L.DomUtil.create('div', 'info legend');
  this.update(0, 1);
  return this._div;
};

legend.update = function (minValue, maxValue) {
  var labels = [];
  var from, to;

  digits = selected_type == 'amenity' ? 6 : 2;

  for (var i = 0; i < colors.length; i++) {
    from = minValue + (maxValue + minValue) * (i / colors.length);
    to = minValue + (maxValue + minValue) * ((i + 1) / colors.length);
    from = parseFloat(from).toFixed(digits);
    to = parseFloat(to).toFixed(digits);

    labels.push(
      '<i style="background:' + colors[i]+ '"></i> ' +
      from + (to ? ' &ndash; ' + to : '+'));
  }

  this._div.innerHTML = labels.join('<br>');
};


function getColor(d, minValue, maxValue) {
  var val = (d - minValue) / (maxValue - minValue);
  var i = Math.floor(val * colors.length)
  return colors[_.clamp(i, 0, colors.length - 1)]
}

// Create map
var map = L.map('container', {
  center: [51.509865, -0.118092], zoom: 4, zoomControl:false  
});  // London
// OpenStreetMap tiling
var tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
});
map.addLayer(tiles);


function highlightFeature (e, prop) {
  var layer = e.target;
  layer.setStyle({ weight: 3, fillOpacity: 0.8 });
  if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) { layer.bringToFront(); };
  info.update(layer.feature.properties, prop);
}

function createGeoJSONLayer(data, prop) {
  var minValue = _.minBy(data.features, 'properties.' + prop).properties[prop]
  var maxValue = _.maxBy(data.features, 'properties.' + prop).properties[prop]
  layer = L.geoJson(data, {
    style: function (feature) {
      return {
        fillColor: getColor(feature.properties[prop], minValue, maxValue),
        color: 'black', weight: 1, opacity: 0.4, fillOpacity: 0.7
      };
    },
    onEachFeature: function (feature, layer) {
      layer.on({
        mouseover: e => highlightFeature(e, prop),
        mouseout: function (e) {  // resetHighlight
          var layer = e.target;
          layer.setStyle({ weight: 1, fillOpacity: 0.7 });
          info.update();
        }
      });
    }
  });
  layer.property = prop;
  layer.minValue = minValue;
  layer.maxValue = maxValue;
  
  return layer;
}

$.getJSON("./data/nuts2_data_simplified.json", function(loaded_data) {
  data = loaded_data;

  var select = document.getElementById("select_type");
  select.value = 'amenity';
  select.onchange = function() {
    selected_type = document.getElementById("select_type").value;
    var layer;
    if (selected_type == 'amenity') {
      console.log('Amenity');
      console.log(logistic_control._layers);
      layers = logistic_control._layers;
      for (var i = 0; i < layers.length; i++){ layers[i].layer.remove(); };
      layer = amenity_control._layers[0].layer;
      amenity_control.addTo(map);
      logistic_control.remove();
    } else if (selected_type == 'logistic_regression') {
      console.log('Logistic Regression');
      layers = amenity_control._layers;
      for (var i = 0; i < layers.length; i++){ layers[i].layer.remove(); };
      layer = logistic_control._layers[0].layer;
      logistic_control.addTo(map);
      amenity_control.remove();
    }
    info.update();
    layer.addTo(map);
    legend.update(layer.minValue, layer.maxValue);
  };

  // Add properties for Logistic regression
  var properties = ['DEFR', 'FRUK', 'UKDE']
  for (var i = 0; i < properties.length; i++) {
    logistic_baseLayers[properties[i]] = createGeoJSONLayer(data, properties[i])
  }
  
  // Add properties for amenities
  properties = ['restaurant', 'parking', 'cafe', 'bank', 'atm', 'fast_food', 'fuel', 'school', 'police'];
  for (var i = 0; i < properties.length; i++) {
    var prop = properties[i]
    amenity_baseLayers[prop.replace('_', ' ')] = createGeoJSONLayer(data, prop);
  }
  
  logistic_control = L.control.layers(logistic_baseLayers, null, { collapsed: false });
  amenity_control = L.control.layers(amenity_baseLayers, null, { collapsed: false });
  info.addTo(map);
  amenity_control.addTo(map);
  legend.addTo(map);
  var layer = amenity_control._layers[0].layer
  layer.addTo(map);
  legend.update(layer.minValue, layer.maxValue);

  map.on('baselayerchange', function(e) {
    console.log('baselayerchange ' + e.layer.property);
    legend.update(e.layer.minValue, e.layer.maxValue);
  });
});
