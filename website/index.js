// control that shows state info on hover
var info = L.control();
var legend;
var amenity_control
var logistic_control;
var logistic_baseLayers = {};
var amenity_baseLayers = {};
var selected_type = 'amenity'
var data_geojson;
var data_bins;


info.onAdd = function (map) {
  this._div = L.DomUtil.create('div', 'info');
  this.update();
  return this._div;
};


//info.update = function (props, key) {
info.update = function (props, key) {  
  var title = selected_type == 'amenity' ? 'Amenity per 1000 People' : 'Logistic Regression';
  var innerHTML = '<h4>' + title + '</h4>'
  if (props) {
    innerHTML += '<b>' + props.name + ', ' + props.country + '<br>';
    if (selected_type == 'amenity') {
      innerHTML += parseFloat(1000 * props[key]).toFixed(3) + ' ' + key + ' per 1000 People.';
    } else {
      innerHTML += parseFloat(100 * props[key]).toFixed(2) + ' %';
    }
  } else {
    innerHTML += "Hover over a region";
  }
  this._div.innerHTML = innerHTML;
};


// Update function for legend
function updateLegend (prop) {
  if (prop) {
    var labels = [];

    if( selected_type == 'amenity') {
      var start_bin = 0.0, end_bin;
      for (var i = 0; i < data_bins.colors.length; i++) {
        end_bin = data_bins.bins[prop][i];
        from = parseFloat(1000 * start_bin).toFixed(4);
        to = parseFloat(1000 * end_bin).toFixed(4);
        labels.push(
          '<i style="background:' + data_bins.colors[i]+ '"></i> ' +
          from + (to ? ' &ndash; ' + to : '+'));
        start_bin = end_bin;
      }
    } else {
      for (var i = 0; i < data_bins.colors.length; i++) {
        from = parseFloat(i / data_bins.colors.length).toFixed(2);
        to = parseFloat((i + 1) / data_bins.colors.length).toFixed(2);
        labels.push(
          '<i style="background:' + data_bins.colors[i]+ '"></i> ' +
          from + (to ? ' &ndash; ' + to : '+'));
      }
    }
    this._div.innerHTML = labels.join('<br>');
  }
};


// Get colors for choropleth map
function getColor(d, prop) {
  if ( data_bins.properties.includes(prop) ) {
    var color_idx = 0;
    for (var i = 0; i < data_bins.colors.length; i++) {
      if ( data_bins.bins[prop][i] < d ){
        color_idx = i + 1;
      }
    }
  } else {
    var color_idx = Math.floor(d * data_bins.colors.length)
  }
  return data_bins.colors[
    _.clamp(color_idx, 0, data_bins.colors.length - 1)]
}


// Create map and tiles
var map = L.map('container', {
  center: [51.509865, -0.118092], zoom: 4, zoomControl:false  
});  // London
// OpenStreetMap tiling
var tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
});
map.addLayer(tiles);


// Create GeoJSON Layer
function createGeoJSONLayer(data, prop) {
  layer = L.geoJson(data, {
    style: function (feature) {
      return {
        fillColor: getColor(feature.properties[prop], prop),
        color: 'black', weight: 1, opacity: 0.4, fillOpacity: 0.7
      };
    },
    onEachFeature: function (feature, layer) {
      layer.on({
        mouseover: function (e) {
          var layer = e.target;
          layer.setStyle({ weight: 3, fillOpacity: 0.8 });
          if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) { 
            layer.bringToFront(); 
          };
          info.update(layer.feature.properties, prop);
        },
        mouseout: function (e) {  // resetHighlight
          var layer = e.target;
          layer.setStyle({ weight: 1, fillOpacity: 0.7 });
          info.update();
        }
      });
    }
  });
  layer.property = prop;
  return layer;
}


// Change between amenity and logistic regression
function selectOnChange() {
  selected_type = document.getElementById("select_type").value;
  var layer;
  if (selected_type == 'amenity') {
    console.log('Amenity');
    console.log(logistic_control._layers);
    layers = logistic_control._layers;
    for (var i = 0; i < layers.length; i++){
      layers[i].layer.remove();
    };
    layer = amenity_control._layers[0].layer;
    amenity_control.addTo(map);
    logistic_control.remove();
  } else if (selected_type == 'logistic_regression') {
    console.log('Logistic Regression');
    layers = amenity_control._layers;
    for (var i = 0; i < layers.length; i++){ 
      layers[i].layer.remove();
    };
    layer = logistic_control._layers[0].layer;
    logistic_control.addTo(map);
    amenity_control.remove();
  }
  info.update();
  layer.addTo(map);
  legend.update(layer.property);
};


fetch("./data/nuts2_amenity_bins.json")
  .then(response => response.json())
  .then(function(loaded_data_bins) {
    data_bins = loaded_data_bins;
    return fetch("./data/nuts2_data_simplified.json")
  })
  .then(response => response.json())
  .then(function(loaded_data_geojson) {
  data_geojson = loaded_data_geojson;
  
  // Prepare dropdown
  var select = document.getElementById("select_type");
  select.value = 'amenity';
  select.onchange = selectOnChange;

  // Add properties for Logistic regression
  var properties = ['DEFR', 'FRUK', 'UKDE']
  for (var i = 0; i < properties.length; i++) {
    logistic_baseLayers[properties[i]] = createGeoJSONLayer(
      data_geojson, properties[i])
  }
  
  // Add properties for amenities
  properties = data_bins.properties;
  for (var i = 0; i < properties.length; i++) {
    var prop = properties[i]
    amenity_baseLayers[prop.replace('_', ' ')] = createGeoJSONLayer(
      data_geojson, prop);
  }

  // Add info
  info.addTo(map);

  // Add control layers to map
  logistic_control = L.control.layers(
    logistic_baseLayers, null, { collapsed: false });
  amenity_control = L.control.layers(
    amenity_baseLayers, null, { collapsed: false });
  amenity_control.addTo(map);
  var layer = amenity_control._layers[0].layer
  layer.addTo(map);

  // Add legend
  legend = L.control({position: 'bottomright'});
  legend.update = updateLegend;
  legend.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info legend');
    this.update();
    return this._div;
  };
  legend.addTo(map);
  legend.update(layer.property);

  map.on('baselayerchange', function(e) {
    console.log('baselayerchange ' + e.layer.property);
    legend.update(e.layer.property);
  });
});
