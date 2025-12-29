let videoElement = null;
function startWebcam() {
  if (videoElement) return;
  videoElement = document.getElementById('video');
  if (!videoElement) return;
  navigator.mediaDevices.getUserMedia({video: true}).then(stream => {
    videoElement.srcObject = stream;
  }).catch(err => {
    console.error('Unable to access webcam', err);
    alert('Cannot access webcam. Please allow camera permission.');
  });
}

async function captureImage() {
  startWebcam();
  const video = document.getElementById('video');
  const canvas = document.getElementById('canvas');
  canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataUrl = canvas.toDataURL('image/png');
  return dataUrl;
}

function getCookie(name) {
  const value = '; ' + document.cookie;
  const parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
}
window.addEventListener('load', startWebcam);
