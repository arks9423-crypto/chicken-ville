// QRMenu — Client-side image compression
// Compresses any image to max 800×800px and JPEG quality 0.75 before base64 encoding

function compressImageToBase64(file, maxWidth, maxHeight, quality, callback) {
  maxWidth  = maxWidth  || 800;
  maxHeight = maxHeight || 800;
  quality   = quality   || 0.75;

  var reader = new FileReader();
  reader.onload = function(e) {
    var img = new Image();
    img.onload = function() {
      var canvas = document.createElement('canvas');
      var w = img.width;
      var h = img.height;

      if (w > maxWidth || h > maxHeight) {
        var ratio = Math.min(maxWidth / w, maxHeight / h);
        w = Math.round(w * ratio);
        h = Math.round(h * ratio);
      }

      canvas.width  = w;
      canvas.height = h;
      var ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, w, h);
      callback(canvas.toDataURL('image/jpeg', quality));
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

// Helper used in templates:
// compressAndPreview(inputEl, previewId, placeholderId, hiddenInputId)
function compressAndPreview(input, previewId, placeholderId, hiddenId) {
  var file = input.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    alert('يرجى اختيار ملف صورة صحيح (JPG، PNG، WEBP)');
    input.value = '';
    return;
  }

  compressImageToBase64(file, 800, 800, 0.78, function(base64) {
    var preview     = document.getElementById(previewId);
    var placeholder = document.getElementById(placeholderId);
    var hidden      = document.getElementById(hiddenId);

    if (preview)     { preview.src = base64; preview.style.display = 'block'; }
    if (placeholder) { placeholder.style.display = 'none'; }
    if (hidden)      { hidden.value = base64; }
  });
}

// Logo — larger allowed (square crop look)
function compressLogo(input, previewId, placeholderId, hiddenId) {
  var file = input.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    alert('يرجى اختيار ملف صورة صحيح');
    input.value = '';
    return;
  }

  compressImageToBase64(file, 400, 400, 0.82, function(base64) {
    var preview     = document.getElementById(previewId);
    var placeholder = document.getElementById(placeholderId);
    var hidden      = document.getElementById(hiddenId);

    if (preview)     { preview.src = base64; preview.style.display = 'block'; }
    if (placeholder) { placeholder.style.display = 'none'; }
    if (hidden)      { hidden.value = base64; }
  });
}
