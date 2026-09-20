export default function BackgroundVideo() {
  return <div className="background" aria-hidden="true">
    <img src="/satquery_hero_bg.png" alt="" />
    <video
      autoPlay
      muted
      loop
      playsInline
      preload="metadata"
      poster="/satquery_hero_bg.png"
      tabIndex={-1}
      disablePictureInPicture
    >
      <source src="https://svs.gsfc.nasa.gov/vis/a010000/a014800/a014858/L9_CloseRotation.mp4" type="video/mp4" />
    </video>
    <div className="background-overlay" />
  </div>;
}
