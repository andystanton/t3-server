from org.threejs import api

renderer = api.WebGLRenderer()
renderer.setSize(window.innerWidth, window.innerHeight)
document.body.appendChild(renderer.domElement)

scene = api.Scene();

geometry = api.BoxGeometry(1, 1, 1)
material = api.MeshLambertMaterial({'color': 0xffffff})
cube = api.Mesh(geometry, material)
scene.add(cube)

ambientLight = api.AmbientLight(0xff00ff, 0.5)
scene.add(ambientLight)

directionalLight0 = api.DirectionalLight(0xff0000, 0.5)
scene.add(directionalLight0);

directionalLight1 = api.DirectionalLight(0x00ff00, 0.5)
directionalLight1.position.set(50, 50, 50)
scene.add(directionalLight1)

camera = api.PerspectiveCamera(30, window.innerWidth/window.innerHeight, 0.1, 1000)
camera.position.z = 5

animationId = -1;

def render():
    nonlocal animationId
    animationId = requestAnimationFrame(render)
    cube.rotation.x += 0.01
    cube.rotation.y += 0.01
    renderer.render(scene, camera)

def stopRender():
    nonlocal animationId
    if (animationId != -1):
        cancelAnimationFrame(animationId)
