package be.cytomine.controller.middleware;

import be.cytomine.controller.RestCytomineController;
import be.cytomine.service.middleware.ImageServerService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;

@RestController
@RequestMapping("/api")
@Slf4j
@RequiredArgsConstructor
public class RestImageServerController extends RestCytomineController {

    private final ImageServerService imageServerService;

    @GetMapping("/imageserver/format.json")
    public ResponseEntity<String> allFormats(
    ) throws IOException {
        log.debug("REST request to list allFormats");
        return responseSuccess(imageServerService.formats());
    }

    @GetMapping("/imageserver/info.json")
    public ResponseEntity<String> serverInfo(
    ) throws IOException {
        log.debug("REST request to get server info");
        return responseSuccess(imageServerService.serverInfo());
    }

    @GetMapping("/imageserver/ui-config.json")
    public ResponseEntity<String> uiConfig(
    ) throws IOException {
        log.debug("REST request to get UI config");
        return responseSuccess(imageServerService.uiConfig());
    }
}
