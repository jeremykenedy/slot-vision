package com.jeremykenedy.reelatrium;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.opengl.Matrix;
import android.preference.PreferenceManager;
import android.view.Choreographer;
import android.view.Surface;
import android.view.SurfaceView;
import com.google.android.filament.Camera;
import com.google.android.filament.ColorGrading;
import com.google.android.filament.Engine;
import com.google.android.filament.EntityManager;
import com.google.android.filament.IndirectLight;
import com.google.android.filament.LightManager;
import com.google.android.filament.MaterialInstance;
import com.google.android.filament.Renderer;
import com.google.android.filament.Scene;
import com.google.android.filament.SwapChain;
import com.google.android.filament.Texture;
import com.google.android.filament.TextureSampler;
import com.google.android.filament.TransformManager;
import com.google.android.filament.View;
import com.google.android.filament.Viewport;
import com.google.android.filament.android.DisplayHelper;
import com.google.android.filament.android.TextureHelper;
import com.google.android.filament.android.UiHelper;
import com.google.android.filament.gltfio.AssetLoader;
import com.google.android.filament.gltfio.FilamentAsset;
import com.google.android.filament.gltfio.Gltfio;
import com.google.android.filament.gltfio.ResourceLoader;
import com.google.android.filament.gltfio.UbershaderProvider;
import com.google.android.filament.utils.KTX1Loader;
import com.google.android.filament.utils.Utils;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Random;

/** Owns the native physically based scene and its Android surface lifecycle. */
public final class ReelSceneView extends SurfaceView implements Choreographer.FrameCallback {
  private final Engine engine;
  private final Renderer renderer;
  private final Scene scene;
  private final View view;
  private final Camera camera;
  private final UiHelper uiHelper;
  private final DisplayHelper displayHelper;
  private final UbershaderProvider materials;
  private final AssetLoader assetLoader;
  private final ResourceLoader resourceLoader;
  private final ColorGrading colorGrading;
  private final int cameraEntity;
  private final int keyEntity;
  private final int[] readyEntities = new int[128];
  private final int[] reelInstances = new int[5];
  private final float[][] reelRest = new float[5][16];
  private final float[] rotation = new float[16];
  private final float[] transform = new float[16];
  private final SharedPreferences preferences;
  private FilamentAsset asset;
  private IndirectLight indirectLight;
  private Texture environmentTexture;
  private Texture seasonAtlas;
  private String activeSeason;
  private int reelSectors;
  private String activeGame;
  private boolean casino;
  private boolean fullscreen;
  private double viewportAspect = 16.0 / 9;
  private final long roundSeed = new Random().nextLong();
  private long roundNumber = Long.MIN_VALUE;
  private ReelRound currentRound;
  private ReelRound previousRound;
  private CoinBurst coins;
  private MaterialInstance beacon;
  private SwapChain swapChain;
  private String settingsSignature;
  private float speed;
  private float lighting;
  private boolean wideCamera;
  private boolean running;
  private boolean destroyed;
  private boolean loading;
  private long startedNanos;
  private long lastFrameNanos;

  public ReelSceneView(Context context) {
    super(context);
    Utils.init();
    Gltfio.init();
    preferences = PreferenceManager.getDefaultSharedPreferences(context);
    engine = Engine.create(Engine.Backend.OPENGL);
    renderer = engine.createRenderer();
    scene = engine.createScene();
    view = engine.createView();
    cameraEntity = EntityManager.get().create();
    camera = engine.createCamera(cameraEntity);
    camera.setExposure(11f, 1f / 125f, 100f);
    view.setScene(scene);
    view.setCamera(camera);
    view.setPostProcessingEnabled(true);
    view.setAntiAliasing(View.AntiAliasing.FXAA);
    view.setDithering(View.Dithering.TEMPORAL);
    view.setShadowingEnabled(false);
    view.setScreenSpaceRefractionEnabled(false);
    View.RenderQuality quality = new View.RenderQuality();
    quality.hdrColorBuffer = View.QualityLevel.LOW;
    view.setRenderQuality(quality);
    colorGrading =
        new ColorGrading.Builder()
            .toneMapping(ColorGrading.ToneMapping.ACES)
            .quality(ColorGrading.QualityLevel.MEDIUM)
            .build(engine);
    view.setColorGrading(colorGrading);
    Renderer.ClearOptions clear = new Renderer.ClearOptions();
    clear.clear = true;
    clear.setClearColor(.008, .011, .015, 1);
    renderer.setClearOptions(clear);
    keyEntity = EntityManager.get().create();
    new LightManager.Builder(LightManager.Type.DIRECTIONAL)
        .color(1f, .88f, .73f)
        .intensity(16000f)
        .direction(-.5f, -1f, -.7f)
        .castShadows(false)
        .build(engine, keyEntity);
    scene.addEntity(keyEntity);
    materials = new UbershaderProvider(engine);
    assetLoader = new AssetLoader(engine, materials, EntityManager.get());
    resourceLoader = new ResourceLoader(engine, true);
    loadEnvironment();
    displayHelper = new DisplayHelper(context);
    uiHelper = new UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK);
    uiHelper.setRenderCallback(
        new UiHelper.RendererCallback() {
          @Override
          public void onNativeWindowChanged(Surface surface) {
            if (swapChain != null) engine.destroySwapChain(swapChain);
            swapChain = engine.createSwapChain(surface);
            displayHelper.attach(renderer, getDisplay());
          }

          @Override
          public void onDetachedFromSurface() {
            displayHelper.detach();
            if (swapChain != null) {
              engine.destroySwapChain(swapChain);
              swapChain = null;
              engine.flushAndWait();
            }
          }

          @Override
          public void onResized(int width, int height) {
            if (height == 0) return;
            view.setViewport(new Viewport(0, 0, width, height));
            viewportAspect = (double) width / height;
            updateProjection();
          }
        });
    uiHelper.setDesiredSize(1280, 720);
    uiHelper.attachTo(this);
  }

  public void start() {
    if (destroyed || running) return;
    String signature = preferences.getAll().toString();
    if (!signature.equals(settingsSignature)) {
      loadSettings();
      settingsSignature = signature;
    }
    running = true;
    lastFrameNanos = 0;
    Choreographer.getInstance().postFrameCallback(this);
  }

  public void stop() {
    running = false;
    Choreographer.getInstance().removeFrameCallback(this);
  }

  public void destroy() {
    if (destroyed) return;
    stop();
    uiHelper.detach();
    unloadModel();
    resourceLoader.destroy();
    assetLoader.destroy();
    materials.destroyMaterials();
    materials.destroy();
    if (indirectLight != null) engine.destroyIndirectLight(indirectLight);
    if (environmentTexture != null) engine.destroyTexture(environmentTexture);
    scene.remove(keyEntity);
    engine.destroyEntity(keyEntity);
    engine.destroyColorGrading(colorGrading);
    engine.destroyView(view);
    engine.destroyRenderer(renderer);
    engine.destroyCameraComponent(cameraEntity);
    engine.destroyScene(scene);
    EntityManager.get().destroy(keyEntity);
    EntityManager.get().destroy(cameraEntity);
    engine.destroy();
    destroyed = true;
  }

  @Override
  public void doFrame(long frameTimeNanos) {
    if (!running || destroyed) return;
    Choreographer.getInstance().postFrameCallback(this);
    if (!uiHelper.isReadyToRender() || swapChain == null) return;
    if (frameTimeNanos - lastFrameNanos < 30_000_000L) return;
    lastFrameNanos = frameTimeNanos;
    if (asset != null) {
      resourceLoader.asyncUpdateLoad();
      int count;
      while ((count = asset.popRenderables(readyEntities)) > 0) {
        for (int i = 0; i < count; i++) {
          if (!"Protective reel glass".equals(asset.getName(readyEntities[i])))
            if (environmentVisible(asset.getName(readyEntities[i])))
              scene.addEntity(readyEntities[i]);
        }
      }
      if (loading && resourceLoader.asyncGetLoadProgress() >= 1f) {
        loading = false;
        applySeason(activeSeason);
        for (MaterialInstance material : asset.getInstance().getMaterialInstances()) {
          String name = material.getName();
          if (name != null && name.startsWith("Trim") && coins == null)
            coins = new CoinBurst(engine, scene, material);
          if (name != null && name.startsWith("Jackpot beacon")) beacon = material;
        }
        asset.releaseSourceData();
      }
    }
    double seconds = (frameTimeNanos - startedNanos) * 1e-9;
    animateReels(seconds);
    if (fullscreen) camera.lookAt(0, 1.035, 3.2, 0, 1.035, 0, 0, 1, 0);
    else {
      double yaw = .26 + Math.sin(seconds * .07) * (wideCamera ? .44 : .30);
      double distance = 3.2 + Math.sin(seconds * .043) * .025;
      camera.lookAt(
          Math.sin(yaw) * distance,
          1.08 + Math.sin(seconds * .051) * .025,
          Math.cos(yaw) * distance,
          Math.sin(seconds * .047) * .08,
          .94 + Math.sin(seconds * .037) * .015,
          0,
          0,
          1,
          0);
    }
    if (renderer.beginFrame(swapChain, frameTimeNanos)) {
      renderer.render(view);
      renderer.endFrame();
    }
  }

  private void loadSettings() {
    Random random = new Random();
    String[] selected = new String[ReelOptions.KEYS.length];
    for (int i = 0; i < selected.length; i++)
      selected[i] =
          ReelOptions.resolve(
              i, preferences.getString(ReelOptions.KEYS[i], ReelOptions.DEFAULTS[i]), random);
    speed = ReelOptions.speed(selected[2]);
    lighting = ReelOptions.light(selected[3]);
    wideCamera = "wide".equals(selected[4]);
    if (indirectLight != null) indirectLight.setIntensity(8000f * lighting);
    int key = engine.getLightManager().getInstance(keyEntity);
    engine.getLightManager().setIntensity(key, 16000f * lighting);
    activeGame = selected[0];
    casino = "casino".equals(selected[5]);
    fullscreen = "fullscreen".equals(selected[6]);
    updateProjection();
    roundNumber = Long.MIN_VALUE;
    reelSectors = "garden".equals(selected[0]) ? 16 : 8;
    loadModel(
        "models/" + (fullscreen ? "fullscreen_" : "") + selected[0] + "_atrium.glb", selected[1]);
    startedNanos = System.nanoTime();
  }

  private void updateProjection() {
    if (fullscreen) {
      double height = "garden".equals(activeGame) ? .76 : "palace".equals(activeGame) ? .63 : .70;
      camera.setProjection(
          Camera.Projection.ORTHO,
          -height * viewportAspect / 2,
          height * viewportAspect / 2,
          -height / 2,
          height / 2,
          .04,
          30);
    } else camera.setProjection(39, viewportAspect, .04, 30, Camera.Fov.VERTICAL);
  }

  private void loadEnvironment() {
    try {
      KTX1Loader.IndirectLightBundle environment =
          KTX1Loader.INSTANCE.createIndirectLight(
              engine, readAsset("ibl/atrium_ibl.ktx"), new KTX1Loader.Options());
      indirectLight = environment.getIndirectLight();
      environmentTexture = environment.getCubemap();
      if (indirectLight == null) throw new IllegalStateException("Invalid lighting environment");
      indirectLight.setIntensity(8000f);
      scene.setIndirectLight(indirectLight);
    } catch (IOException error) {
      throw new IllegalStateException("The lighting environment is missing", error);
    }
  }

  private void loadModel(String filename, String season) {
    unloadModel();
    try {
      asset = assetLoader.createAsset(readAsset(filename));
    } catch (IOException error) {
      throw new IllegalStateException("The cabinet model is missing: " + filename, error);
    }
    if (asset == null) throw new IllegalStateException("Invalid cabinet model: " + filename);
    if (asset.getResourceUris().length != 0)
      throw new IllegalStateException("Cabinet resources must be embedded");
    loading = resourceLoader.asyncBeginLoad(asset);
    if (!loading) throw new IllegalStateException("Could not load cabinet resources");
    TransformManager transforms = engine.getTransformManager();
    for (int i = 0; i < reelInstances.length; i++) {
      int entity = asset.getFirstEntityByName("Reel_" + i);
      reelInstances[i] = entity == 0 ? 0 : transforms.getInstance(entity);
      if (reelInstances[i] != 0) transforms.getTransform(reelInstances[i], reelRest[i]);
    }
    activeSeason = season;
  }

  private void unloadModel() {
    if (asset == null) return;
    if (coins != null) {
      coins.destroy();
      coins = null;
    }
    beacon = null;
    resourceLoader.asyncCancelLoad();
    scene.removeEntities(asset.getEntities());
    assetLoader.destroyAsset(asset);
    resourceLoader.evictResourceData();
    asset = null;
    if (seasonAtlas != null) {
      engine.destroyTexture(seasonAtlas);
      seasonAtlas = null;
    }
    loading = false;
  }

  private boolean environmentVisible(String name) {
    if (name == null) return true;
    if (name.equals("Coin_material_source")) return false;
    if (name.startsWith("Casino_")) return casino;
    if (name.startsWith("Lounge_")) return !casino;
    return true;
  }

  private void animateReels(double seconds) {
    int columns = ReelOptions.columns(activeGame);
    double duration = ReelRound.roundDuration(columns, speed);
    long round = (long) Math.floor(seconds / duration);
    double phase = (seconds - round * duration) * speed;
    if (round != roundNumber) {
      previousRound = new ReelRound(roundSeed, round - 1, columns, ReelOptions.rows(activeGame));
      currentRound = new ReelRound(roundSeed, round, columns, ReelOptions.rows(activeGame));
      roundNumber = round;
    }
    TransformManager transforms = engine.getTransformManager();
    transforms.openLocalTransformTransaction();
    for (int i = 0; i < columns; i++) {
      if (reelInstances[i] == 0) continue;
      float angle =
          (float)
              ((currentRound.position(previousRound, phase, i) % reelSectors)
                  * (360.0 / reelSectors));
      Matrix.setRotateM(rotation, 0, angle, 1, 0, 0);
      Matrix.multiplyMM(transform, 0, reelRest[i], 0, rotation, 0);
      transforms.setTransform(reelInstances[i], transform);
    }
    transforms.commitLocalTransformTransaction();
    double celebrationAge = (phase - ReelRound.settledAt(columns)) / speed;
    if (coins != null)
      coins.update(
          celebrationAge,
          currentRound.jackpot() ? 64 : ReelRound.coinCount(currentRound.payout),
          currentRound.celebrationDuration(),
          round,
          fullscreen);
    if (beacon != null) {
      float pulse =
          currentRound.jackpot() && celebrationAge >= 0 && celebrationAge < 10
              ? Math.max(0f, (float) Math.sin(celebrationAge * 9))
              : 0f;
      beacon.setParameter("emissiveFactor", pulse * 12000f, pulse * 180f, pulse * 80f);
    }
  }

  private void applySeason(String season) {
    float[] trim = null;
    float[] accent = {.08f, .65f, .54f};
    if ("spring".equals(season)) {
      trim = new float[] {.90f, .61f, .48f};
      accent = new float[] {.95f, .23f, .48f};
    }
    if ("summer".equals(season)) {
      trim = new float[] {.95f, .74f, .30f};
      accent = new float[] {.04f, .65f, .88f};
    }
    if ("autumn".equals(season)) {
      trim = new float[] {.88f, .45f, .25f};
      accent = new float[] {.95f, .24f, .035f};
    }
    if ("winter".equals(season)) {
      trim = new float[] {.91f, .92f, .95f};
      accent = new float[] {.17f, .55f, 1f};
    }
    TextureSampler sampler =
        new TextureSampler(
            TextureSampler.MinFilter.LINEAR_MIPMAP_LINEAR,
            TextureSampler.MagFilter.LINEAR,
            TextureSampler.WrapMode.REPEAT);
    sampler.setAnisotropy(4f);
    if (fullscreen) sampler.setWrapModeS(TextureSampler.WrapMode.CLAMP_TO_EDGE);
    if ("classic".equals(activeGame)) seasonAtlas = loadSeasonAtlas("classic");
    else if (fullscreen || !"atrium".equals(season)) seasonAtlas = loadSeasonAtlas(season);
    for (MaterialInstance material : asset.getInstance().getMaterialInstances()) {
      String name = material.getName();
      if (name == null) continue;
      if (name.startsWith("ReelPaper") && seasonAtlas != null)
        material.setParameter("baseColorMap", seasonAtlas, sampler);
      if (name.startsWith("Trim") && trim != null)
        material.setParameter("baseColorFactor", trim[0], trim[1], trim[2], 1f);
      if (name.startsWith("Accent"))
        material.setParameter("emissiveFactor", accent[0] * 3f, accent[1] * 3f, accent[2] * 3f);
    }
  }

  private Texture loadSeasonAtlas(String season) {
    final Bitmap bitmap;
    try (InputStream input = getContext().getAssets().open("textures/symbols_" + season + ".png")) {
      BitmapFactory.Options options = new BitmapFactory.Options();
      options.inScaled = false;
      options.inPreferredConfig = Bitmap.Config.ARGB_8888;
      bitmap = BitmapFactory.decodeStream(input, null, options);
    } catch (IOException error) {
      throw new IllegalStateException("Seasonal reel artwork is missing", error);
    }
    if (bitmap == null || bitmap.getWidth() != 512 || bitmap.getHeight() != 4096)
      throw new IllegalStateException("Invalid seasonal reel artwork");
    Texture texture =
        new Texture.Builder()
            .width(512)
            .height(4096)
            .levels(0xff)
            .sampler(Texture.Sampler.SAMPLER_2D)
            .format(Texture.InternalFormat.SRGB8_A8)
            .usage(Texture.Usage.DEFAULT | Texture.Usage.GEN_MIPMAPPABLE)
            .build(engine);
    TextureHelper.setBitmap(
        engine,
        texture,
        0,
        bitmap,
        null,
        new Runnable() {
          @Override
          public void run() {
            bitmap.recycle();
          }
        });
    texture.generateMipmaps(engine);
    return texture;
  }

  private ByteBuffer readAsset(String name) throws IOException {
    try (InputStream input = getContext().getAssets().open(name);
        ByteArrayOutputStream output = new ByteArrayOutputStream()) {
      byte[] chunk = new byte[16384];
      int count;
      while ((count = input.read(chunk)) != -1) output.write(chunk, 0, count);
      byte[] bytes = output.toByteArray();
      ByteBuffer buffer = ByteBuffer.allocateDirect(bytes.length).order(ByteOrder.nativeOrder());
      buffer.put(bytes).flip();
      return buffer;
    }
  }
}
