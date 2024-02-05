$(document).ready(function(){
  var statusClasses = {
    "Queued": {"li": "bg-secondary", "a": "link-light"},
    "Processing": {"li": "bg-warning", "a": "link-dark"},
    "Complete": {"li": "bg-success", "a": "link-light"},
    "Failed": {"li": "bg-danger", "a": "link-light"}
  }
  console.error("Load")
  $('#conversions li').each(function(i, elem){
    $(elem).addClass(statusClasses[$(elem).attr("status")]["li"] + " mb-1")
  });
  $('#conversions a').each(function(i, elem){
    $(elem).addClass(statusClasses[$(elem).attr("status")]["a"])
  });
})
